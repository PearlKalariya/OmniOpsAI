import logging

from fastapi import APIRouter, Depends, HTTPException

from app.agents.graph import agent_graph
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.agent import AgentAskRequest, AgentAskResponse
from app.services import llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/ask", response_model=AgentAskResponse)
def agent_ask(payload: AgentAskRequest, current_user: User = Depends(get_current_user)):
    if not llm.is_configured():
        raise HTTPException(status_code=503, detail="LLM not configured: set LLM_API_KEY in backend/.env")

    try:
        state = agent_graph.invoke({"question": payload.question, "owner_id": current_user.id})
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
    )
