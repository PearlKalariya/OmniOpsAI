import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.agents.graph import agent_graph
from app.api.deps import get_current_user
from app.connectors import slack
from app.connectors.base import ConnectorError
from app.core.ratelimit import limiter
from app.models.user import User
from app.schemas.agent import AgentAskRequest, AgentAskResponse, AgentReportRequest
from app.services import llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


def _run_graph(initial_state: dict) -> AgentAskResponse:
    try:
        state = agent_graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Agent graph failed")
        raise HTTPException(status_code=502, detail=f"Agent run failed ({type(exc).__name__}); see server logs") from exc

    if not state.get("hits"):
        raise HTTPException(status_code=404, detail="No relevant documents found for this question")

    return AgentAskResponse(
        answer=state.get("answer"),
        model=state.get("model"),
        plan=state.get("plan", {}),
        verification=state.get("verification"),
        sources=state.get("hits", []),
        trace=state.get("trace", []),
        report=state.get("report"),
        report_format=state.get("report_format"),
    )


@router.post("/ask", response_model=AgentAskResponse)
@limiter.limit("10/minute")  # one agent run = 3 LLM calls (planner/answer/verifier)
def agent_ask(request: Request, payload: AgentAskRequest, current_user: User = Depends(get_current_user)):
    if not llm.is_configured():
        raise HTTPException(status_code=503, detail="LLM not configured: set LLM_API_KEY in backend/.env")
    return _run_graph({"question": payload.question, "owner_id": current_user.id})


@router.post("/report", response_model=AgentAskResponse)
@limiter.limit("10/minute")  # 4 LLM calls (adds report formatting)
def agent_report(request: Request, payload: AgentReportRequest, current_user: User = Depends(get_current_user)):
    if not llm.is_configured():
        raise HTTPException(status_code=503, detail="LLM not configured: set LLM_API_KEY in backend/.env")
    result = _run_graph(
        {"question": payload.question, "owner_id": current_user.id, "report_format": payload.format}
    )

    if payload.slack_channel and payload.format == "slack" and result.report:
        if not slack.is_configured():
            raise HTTPException(status_code=503, detail="Slack connector not configured")
        try:
            slack.send_message(payload.slack_channel, result.report)
            result.delivered_to = payload.slack_channel
        except ConnectorError as exc:
            # Report succeeded; delivery didn't. Surface both.
            raise HTTPException(status_code=502, detail=f"Report generated but Slack delivery failed: {exc}") from exc
    return result
