"""Shared state flowing through the agent graph.

Each node reads what it needs and returns a partial update; LangGraph
merges updates into the state. `trace` accumulates one entry per node so
API responses can show what the agent actually did (portfolio: agent
execution visibility, feeds the M3 Agent Execution Graph UI).
"""

import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    # inputs
    question: str
    owner_id: str

    # planner output
    plan: dict[str, Any]  # {"mode": "hybrid|bm25|vector", "limit": int, "reason": str}

    # retrieval output
    hits: list[dict]

    # answer output
    answer: str
    model: str

    # verifier output
    verification: dict[str, Any]  # {"grounded": bool, "notes": str}

    # accumulated node trace: [{"node": ..., "ms": ..., **extras}]
    trace: Annotated[list[dict], operator.add]
