from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.document import SearchHit

ReportFormat = Literal["summary", "report", "ticket", "slack", "email"]


class AgentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AgentReportRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    format: ReportFormat = "summary"
    # When set (and format == "slack"), the report is also posted to this
    # Slack channel via the Slack connector.
    slack_channel: str | None = Field(default=None, max_length=100)


class AgentAskResponse(BaseModel):
    answer: str | None
    model: str | None = None
    plan: dict[str, Any]
    verification: dict[str, Any] | None = None
    sources: list[SearchHit] = []
    trace: list[dict[str, Any]] = []
    report: str | None = None
    report_format: str | None = None
    delivered_to: str | None = None  # slack channel when delivery happened
