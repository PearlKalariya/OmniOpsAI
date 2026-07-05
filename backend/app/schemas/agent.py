from typing import Any

from pydantic import BaseModel, Field

from app.schemas.document import SearchHit


class AgentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AgentAskResponse(BaseModel):
    answer: str | None
    model: str | None = None
    plan: dict[str, Any]
    verification: dict[str, Any] | None = None
    sources: list[SearchHit] = []
    trace: list[dict[str, Any]] = []
