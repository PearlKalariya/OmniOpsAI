"""Agent graph nodes: planner -> retrieve -> answer -> verify.

Every node is a plain function of AgentState returning a partial update.
LLM-dependent nodes degrade gracefully: planner falls back to a default
plan, verifier to "unverified" — a broken/missing LLM never kills the run
mid-graph (the answer node is the exception: without an LLM there is no
product, so its error propagates).
"""

import logging
import time

from app.agents.state import AgentState
from app.services import hybrid, llm, search, vectorstore
from app.services.embeddings import embed_query

logger = logging.getLogger(__name__)

MAX_LIMIT = 20
DEFAULT_PLAN = {"mode": "hybrid", "limit": 5, "reason": "default plan"}

PLANNER_SYSTEM = (
    "You are the planner of a document-QA agent. Decide how to retrieve "
    "context for the user's question. Reply with ONLY a JSON object: "
    '{"mode": "hybrid"|"bm25"|"vector", "limit": <1-20>, "reason": "<short>"}. '
    "Guidance: bm25 for exact identifiers/codes/names, vector for paraphrased "
    "or conceptual questions, hybrid when unsure (safe default). limit: 3-5 "
    "for narrow factual questions, 8-12 for summaries/overviews."
)

VERIFIER_SYSTEM = (
    "You are a strict fact-checker. Given numbered context passages and an "
    "answer, judge whether every factual claim in the answer is supported by "
    "the passages. Reply with ONLY a JSON object: "
    '{"grounded": true|false, "notes": "<one sentence>"}.'
)


def plan_node(state: AgentState) -> dict:
    start = time.monotonic()
    try:
        raw = llm.complete_json(PLANNER_SYSTEM, f"Question: {state['question']}")
        mode = raw.get("mode") if raw.get("mode") in ("hybrid", "bm25", "vector") else "hybrid"
        limit = max(1, min(int(raw.get("limit", 5)), MAX_LIMIT))
        plan = {"mode": mode, "limit": limit, "reason": str(raw.get("reason", ""))[:200]}
    except Exception as exc:
        logger.warning("Planner LLM failed, using default plan: %s", exc)
        plan = DEFAULT_PLAN
    ms = int((time.monotonic() - start) * 1000)
    return {"plan": plan, "trace": [{"node": "planner", "ms": ms, "plan": plan}]}


def retrieve_node(state: AgentState) -> dict:
    start = time.monotonic()
    plan = state.get("plan", DEFAULT_PLAN)
    owner_id, question = state["owner_id"], state["question"]
    mode, limit = plan["mode"], plan["limit"]

    if mode == "bm25":
        hits = search.search_chunks(owner_id=owner_id, query=question, size=limit)
    elif mode == "vector":
        hits = vectorstore.search_chunks(owner_id=owner_id, query_vector=embed_query(question), size=limit)
    else:
        hits = hybrid.hybrid_search(owner_id=owner_id, query=question, size=limit)

    ms = int((time.monotonic() - start) * 1000)
    return {"hits": hits, "trace": [{"node": "retrieval", "ms": ms, "mode": mode, "hits": len(hits)}]}


def answer_node(state: AgentState) -> dict:
    start = time.monotonic()
    result = llm.generate_answer(question=state["question"], chunks=state["hits"])
    ms = int((time.monotonic() - start) * 1000)
    return {
        "answer": result["answer"],
        "model": result["model"],
        "trace": [{"node": "answer", "ms": ms, "model": result["model"]}],
    }


def verify_node(state: AgentState) -> dict:
    start = time.monotonic()
    context = "\n\n".join(f"[{i + 1}] {h['content']}" for i, h in enumerate(state["hits"]))
    try:
        raw = llm.complete_json(
            VERIFIER_SYSTEM,
            f"Context passages:\n\n{context}\n\nAnswer to check:\n{state['answer']}",
        )
        verification = {"grounded": bool(raw.get("grounded")), "notes": str(raw.get("notes", ""))[:300]}
    except Exception as exc:
        logger.warning("Verifier LLM failed: %s", exc)
        verification = {"grounded": None, "notes": "verification unavailable"}
    ms = int((time.monotonic() - start) * 1000)
    return {"verification": verification, "trace": [{"node": "verifier", "ms": ms, **verification}]}
