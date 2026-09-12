import re
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.core.config import settings
from app.models import AgentState
from app.tools.product_tools import search_product, list_all_products
from app.core.llm import get_llm

llm = get_llm()


tools = [search_product, list_all_products]

SYSTEM_PROMPT = """You are the Product Knowledge Agent for DishTV ('DishBot').
Your job is to answer user questions about DishTV set-top boxes, smart devices, features, packages, and pricing.

You have access to live MongoDB tools:
- search_product(query): Search by keyword/name for specific items.
- list_all_products(category): Retrieve all hardware or packages when asked broadly.

Rules:
1. If the user refers to pronouns like 'it', 'this box', or 'the pack', look at the previous messages to resolve the entity.
2. If a search yields no results, formulate a different search query or list products to locate the right info.
3. Every final response discussing a product MUST include the official source_url link from the database.
"""


product_agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT
)

async def product_knowledge_node(state: AgentState) -> dict:
    """
    Executes the autonomous Product Agent (ReAct loop: Reason -> Act -> Observe).
    """

    result = await product_agent.ainvoke({"messages": state.messages})
    

    last_ai_message = result["messages"][-1]
    content = last_ai_message.content

    # Normalize content if Gemini returned a list of content blocks
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            else:
                text_parts.append(str(part))
        content = "\n".join(text_parts)
    else:
        content = str(content)

    # Extract source_url for API output
    source_url = None
    match = re.search(r'https?://[^\s)\]]+', content)
    if match:
        source_url = match.group(0)

    return {
        "messages": [AIMessage(content=content)],
        "source_url": source_url
    }

