"""Evaluation endpoints.

Run an eval over a set of questions (POST /run), then read aggregate
metrics and per-question breakdown. Eval is a synchronous multi-LLM job
(agent graph + judge per question), so it's rate-limited hard.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.ratelimit import limiter
from app.db.session import get_db
from app.models.evaluation import EvalRun
from app.models.user import User
from app.schemas.evaluation import EvalRunDetail, EvalRunOut, EvalRunRequest
from app.services import evaluation, llm

router = APIRouter(prefix="/api/eval", tags=["evaluation"])


@router.post("/run", response_model=EvalRunDetail)
@limiter.limit("3/minute")  # each question = agent run + judge (many LLM calls)
def run_eval(payload: EvalRunRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not llm.is_configured():
        raise HTTPException(status_code=503, detail="LLM not configured: set LLM_API_KEY in backend/.env")

    items = [item.model_dump() for item in payload.items]
    try:
        return evaluation.run_eval(db, owner_id=current_user.id, dataset_name=payload.dataset_name, items=items)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Eval run failed ({type(exc).__name__}); see server logs") from exc


@router.get("", response_model=list[EvalRunOut])
def list_runs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(EvalRun)
        .filter(EvalRun.owner_id == current_user.id)
        .order_by(EvalRun.created_at.desc())
        .all()
    )


@router.get("/{run_id}", response_model=EvalRunDetail)
def get_run(run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    run = db.get(EvalRun, run_id)
    if run is None or run.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return run
