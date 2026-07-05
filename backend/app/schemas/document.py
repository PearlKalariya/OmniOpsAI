from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    status: str
    created_at: datetime
    size_bytes: int | None = None
    page_count: int | None = None
    char_count: int | None = None
    chunk_count: int | None = None


class SearchHit(BaseModel):
    chunk_id: str
    score: float
    document_id: str
    chunk_index: int
    content: str
    sources: list[str] = []  # which retrievers found it (hybrid mode only)
    rerank_score: float | None = None  # cross-encoder score when reranked


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = 5


class AskResponse(BaseModel):
    answer: str
    model: str
    sources: list[SearchHit]
