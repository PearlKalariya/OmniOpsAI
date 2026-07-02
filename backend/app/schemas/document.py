from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchHit(BaseModel):
    chunk_id: str
    score: float
    document_id: str
    chunk_index: int
    content: str
    sources: list[str] = []  # which retrievers found it (hybrid mode only)
