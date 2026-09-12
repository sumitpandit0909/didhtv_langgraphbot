from langchain_core.messages import AIMessage, SystemMessage
# from langchain_google_genai import ChatGoogleGenerativeAI

from app.models import AgentState
from app.database.connection import recharge_history_collection
from app.core.llm import get_llm

llm = get_llm()

HISTORY_FORMATTER_PROMPT = """You are DishBot.
You have retrieved the following transaction records from MongoDB for user {user_id}.
Summarize the last 5 transactions clearly for the user.
Include date, package name, amount (₹), transaction ID, and status.
If the list is empty, inform the user politely that no prior recharge records were found for their account.

Database Records:
{records}
"""

async def history_node(state: AgentState) -> dict:
    """
    Queries MongoDB recharge_history_collection for the user's past 5 transactions and formats the response.
    """
    effective_user_id = state.user_id

    # Fetch last 5 records sorted by date descending
    cursor = recharge_history_collection.find(
        {"user_id": effective_user_id}
    ).sort("date", -1).limit(5)
    
    records = await cursor.to_list(length=5)

    # Format records into clean text for LLM synthesis
    if not records:
        records_text = "No records found."
    else:
        formatted_list = []
        for r in records:
            dt = r.get("date")
            date_str = dt.strftime("%d %b %Y, %I:%M %p") if hasattr(dt, "strftime") else str(dt)
            formatted_list.append(
                f"- Txn ID: {r.get('txn_id', 'N/A')} | Date: {date_str} | Package: {r.get('package', 'N/A')} | Amount: ₹{r.get('amount', 0)} | Status: {r.get('status', 'SUCCESS')}"
            )
        records_text = "\n".join(formatted_list)

    prompt = [
        SystemMessage(content=HISTORY_FORMATTER_PROMPT.format(
            user_id=effective_user_id,
            records=records_text
        )),
        *state.messages
    ]

    response = await llm.ainvoke(prompt)

    return {
        "messages": [AIMessage(content=response.content)]
    }
