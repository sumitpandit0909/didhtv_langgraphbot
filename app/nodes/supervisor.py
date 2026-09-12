from langchain_core.messages import SystemMessage


from app.core.config import settings
from app.models import AgentState,RouteDecision
from app.core.llm import get_llm

llm = get_llm()

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Router for DishTV ('DishBot').
Analyze the conversation history and classify the user intent into one specialized worker:

- 'product_inquiry': Info, features, pricing, or catalog questions for set-top boxes OR recharge packs (e.g. 'What packs are available?', 'Tell me about Dish HD', 'Flexi pack pricing').
- 'recharge_request': Active intent to PAY, RECHARGE, or RENEW an account (e.g. 'Recharge my TV', 'Pay 249', 'Recharge now'). Do NOT use for general plan inquiries.
- 'company_info': Questions about TechChefz Digital (services, team, locations, case studies).
- 'history_check': Past recharges, payment records, or transaction history.
- 'technical_troubleshoot': Signal loss, Error 101/102/301, black screen, remote issues, or hardware diagnostics.
- 'escalate_support': User demands human/agent or reports repeated failures.
- 'general_chat': Greetings, pleasantries, or general bot capabilities.

State your reasoning briefly, then return the chosen next_node.
"""



async def supervisor_node(state:AgentState)->dict:
    """
    Supervisor node that determines the next worker node to execute.
    """
    if state.awaiting_recharge_confirmation:
        return {"next_node":"recharge_request"}
    
    router_llm =llm.with_structured_output(RouteDecision)

    prompt =[
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        *state.messages
    ]

    decision : RouteDecision = await router_llm.ainvoke(prompt)

    return {
        "next_node":decision.next_node
    }

