"""Evaluation runner: dataset -> agent -> judge -> metrics -> persist.

Each dataset item is {"question": str, "expected": str?}. For every item
we run the full agent graph (planner/retrieval/rerank/answer/verify),
score the answer with the judge LLM, and store a per-question row. Run
aggregates are the means of the available metric values.
"""

import time
from statistics import fmean

from sqlalchemy.orm import Session

from app.agents.graph import agent_graph
from app.core.config import settings
from app.models.evaluation import EvalResult, EvalRun
from app.services import judge


def _mean(values: list[float]) -> float | None:
    present = [v for v in values if v is not None]
    return round(fmean(present), 3) if present else None


def run_eval(db: Session, owner_id: str, dataset_name: str, items: list[dict]) -> EvalRun:
    run = EvalRun(
        owner_id=owner_id,
        dataset_name=dataset_name,
        model=settings.llm_model,
        num_questions=len(items),
    )
    db.add(run)
    db.flush()  # assign run.id

    faith, relevance, precision, latencies = [], [], [], []

    for item in items:
        question = item["question"]
        expected = item.get("expected")

        start = time.monotonic()
        state = agent_graph.invoke({"question": question, "owner_id": owner_id})
        latency_ms = int((time.monotonic() - start) * 1000)

        answer = state.get("answer")
        hits = state.get("hits", [])
        contexts = [h["content"] for h in hits]
        grounded = (state.get("verification") or {}).get("grounded")

        scores = (
            judge.score(question, answer, contexts, expected)
            if answer and contexts
            else {"faithfulness": None, "answer_relevance": None, "context_precision": None, "notes": "no answer/context"}
        )

        db.add(
            EvalResult(
                run_id=run.id,
                question=question,
                expected=expected,
                answer=answer,
                faithfulness=scores["faithfulness"],
                answer_relevance=scores["answer_relevance"],
                context_precision=scores["context_precision"],
                grounded=grounded,
                latency_ms=latency_ms,
                notes=scores["notes"],
            )
        )
        faith.append(scores["faithfulness"])
        relevance.append(scores["answer_relevance"])
        precision.append(scores["context_precision"])
        latencies.append(latency_ms)

    run.avg_faithfulness = _mean(faith)
    run.avg_answer_relevance = _mean(relevance)
    run.avg_context_precision = _mean(precision)
    run.avg_latency_ms = _mean(latencies)
    db.commit()
    db.refresh(run)
    return run
