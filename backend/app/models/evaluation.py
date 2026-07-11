import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class EvalRun(Base):
    """One evaluation run over a dataset of questions."""

    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    num_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    # Aggregate metrics (means across questions), 0..1.
    avg_faithfulness: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_answer_relevance: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_context_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    results: Mapped[list["EvalResult"]] = relationship()


class EvalResult(Base):
    """Per-question result within an eval run."""

    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("eval_runs.id"), index=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    faithfulness: Mapped[float | None] = mapped_column(Float, nullable=True)
    answer_relevance: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    grounded: Mapped[bool | None] = mapped_column(nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
