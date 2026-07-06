"""Agent graph assembly.

    planner -> retrieval -> answer -> verifier -> report -> END
                     \\-> END (nothing retrieved)   \\-> END (no report requested)

The report node runs only when the request set `report_format` in the
initial state. Compiled once at import; the compiled graph is stateless
and reusable across requests.
"""

from langgraph.graph import END, StateGraph

from app.agents.nodes import answer_node, plan_node, report_node, retrieve_node, verify_node
from app.agents.state import AgentState


def _after_retrieval(state: AgentState) -> str:
    return "answer" if state.get("hits") else END


def _after_verifier(state: AgentState) -> str:
    return "report" if state.get("report_format") else END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner", plan_node)
    graph.add_node("retrieval", retrieve_node)
    graph.add_node("answer", answer_node)
    graph.add_node("verifier", verify_node)
    graph.add_node("report", report_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "retrieval")
    graph.add_conditional_edges("retrieval", _after_retrieval, {"answer": "answer", END: END})
    graph.add_edge("answer", "verifier")
    graph.add_conditional_edges("verifier", _after_verifier, {"report": "report", END: END})
    graph.add_edge("report", END)
    return graph.compile()


agent_graph = build_graph()
