import random
from langchain_core.messages import AIMessage
from app.models import AgentState

async def escalation_node(state: AgentState) -> dict:
    """
    Generates a support ticket and hands off the conversation to a human executive.
    """
    # Generate random 6-digit ticket ID
    ticket_id = f"#{random.randint(100000, 999999)}"

    # Determine reason for escalation
    if state.repetitive_issue_counter >= 2:
        reason = "I notice you are having repeated difficulties."
    elif state.sentiment_score == "negative":
        reason = "I apologize for any frustration caused."
    else:
        reason = "As requested, I am escalating your query."

    escalation_message = (
        f"{reason} I am connecting you with a live DishTV support executive.\n\n"
        f"📋 **Your Ticket ID is {ticket_id}**\n\n"
        f"An agent will join this chat momentarily to assist you directly. Thank you for your patience!"
    )

    return {
        "messages": [AIMessage(content=escalation_message)],
        "repetitive_issue_counter": 0  # Reset counter
    }
