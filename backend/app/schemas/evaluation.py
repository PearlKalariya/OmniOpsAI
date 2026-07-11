from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvalItem(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    expected: str | None = Field(default=None, max_length=4000)


class EvalRunRequest(BaseModel):
    dataset_name: str = Field(default="custom", max_length=100)
    items: list[EvalItem] = Field(min_length=1, max_length=50)


class EvalResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question: str
    expected: str | None
    answer: str | None
    faithfulness: float | None
    answer_relevance: float | None
    context_precision: float | None
    grounded: bool | None
    latency_ms: int | None
    notes: str | None


class EvalRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_name: str
    model: str
    num_questions: int
    avg_faithfulness: float | None
    avg_answer_relevance: float | None
    avg_context_precision: float | None
    avg_latency_ms: float | None
    created_at: datetime


class EvalRunDetail(EvalRunOut):
    results: list[EvalResultOut] = []
