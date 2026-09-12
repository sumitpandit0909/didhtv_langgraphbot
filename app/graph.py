# app/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.models import AgentState
from app.nodes.supervisor import supervisor_node
from app.nodes.product_knowledge import product_knowledge_node
from app.nodes.techchefz_rag import techchefz_rag_node
from app.nodes.recharge import recharge_node
from app.nodes.history import history_node
from app.nodes.escalation import escalation_node
from app.nodes.general_chat import general_chat_node
from app.nodes.troubleshooting import troubleshooting_node

# 1. Initialize StateGraph with our Pydantic AgentState
workflow = StateGraph(AgentState)

# 2. Add all 7 Nodes (Supervisor + 6 Workers)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("product_inquiry", product_knowledge_node)
workflow.add_node("company_info", techchefz_rag_node)
workflow.add_node("recharge_request", recharge_node)
workflow.add_node("history_check", history_node)
workflow.add_node("escalate_support", escalation_node)
workflow.add_node("general_chat", general_chat_node)
workflow.add_node("technical_troubleshoot", troubleshooting_node)

# 3. Set the Supervisor as the Entry Point
workflow.set_entry_point("supervisor")

# 4. Conditional Edge Router
def route_to_worker(state: AgentState) -> str:
    """
    Routes to the worker node determined by the supervisor.
    Fallback to general_chat if next_node is somehow missing.
    """
    return state.next_node or "general_chat"

workflow.add_conditional_edges(
    "supervisor",
    route_to_worker,
    {
        "product_inquiry": "product_inquiry",
        "company_info": "company_info",
        "recharge_request": "recharge_request",
        "history_check": "history_check",
        "escalate_support": "escalate_support",
        "technical_troubleshoot": "technical_troubleshoot",
        "general_chat": "general_chat",
    }
)

# 5. Workers return to END after completing their turn
WORKER_NODES = [
    "product_inquiry",
    "company_info",
    "recharge_request",
    "history_check",
    "escalate_support",
    "technical_troubleshoot",
    "general_chat"
]

for worker in WORKER_NODES:
    workflow.add_edge(worker, END)


checkpointer = MemorySaver()


dishbot_graph = workflow.compile(checkpointer=checkpointer)
