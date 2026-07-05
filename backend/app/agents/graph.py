"""Agent graph assembly.

    planner -> retrieval -> answer -> verifier -> END
                     \\-> END (when nothing was retrieved)

Compiled once at import; the compiled graph is stateless and reusable
across requests.
"""

from langgraph.graph import END, StateGraph

from app.agents.nodes import answer_node, plan_node, retrieve_node, verify_node
from app.agents.state import AgentState


def _after_retrieval(state: AgentState) -> str:
    return "answer" if state.get("hits") else END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner", plan_node)
    graph.add_node("retrieval", retrieve_node)
    graph.add_node("answer", answer_node)
    graph.add_node("verifier", verify_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "retrieval")
    graph.add_conditional_edges("retrieval", _after_retrieval, {"answer": "answer", END: END})
    graph.add_edge("answer", "verifier")
    graph.add_edge("verifier", END)
    return graph.compile()


agent_graph = build_graph()
