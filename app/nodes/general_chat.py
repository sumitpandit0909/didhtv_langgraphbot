from langchain_core.messages import AIMessage, SystemMessage

from app.models import AgentState
from app.core.llm import get_llm

llm = get_llm()
GENERAL_CHAT_PROMPT = """You are DishBot, the smart virtual assistant for DishTV India.
You can help customers with:
1. Product specs, set-top boxes, smart TV keys, and hardware.
2. Checking recharge packages and processing TV recharges.
3. Viewing previous recharge and transaction history.
4. Technical support or connecting to a live human agent.
5. Inquiries regarding TechChefz Digital (our digital solutions partner).

Respond politely, warmly, and concisely to greetings, compliments, or general queries. Guide the user on what you can do.
"""

async def general_chat_node(state: AgentState) -> dict:
    prompt = [
        SystemMessage(content=GENERAL_CHAT_PROMPT),
        *state.messages
    ]
    response = await llm.ainvoke(prompt)
    return {
        "messages": [AIMessage(content=response.content)]
    }
