import uuid
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.types import interrupt

from app.models import AgentState, RechargeSlots
from app.database.connection import recharge_history_collection
from app.tools.recharge_tools import get_all_recharge_packages, lookup_package_and_price
from app.core.llm import get_llm

llm = get_llm(temperature=0)

class ExtractedRechargeDetails(BaseModel):
    amount: Optional[int] = Field(None, description="Recharge amount in INR if mentioned (e.g. 191, 249, 499).")
    package_name: Optional[str] = Field(None, description="Name of the pack/plan if mentioned (e.g. 'Super Family', 'Flexi HD', 'Swagat Combo').")
    user_id: Optional[str] = Field(None, description="User ID or VC number if mentioned.")

EXTRACTION_SYSTEM_PROMPT = """You are an entity extractor for DishTV recharges.
Extract the package_name, amount, or user_id from the latest user message.
If a parameter is not explicitly mentioned, return null.
"""

async def perform_recharge(user_id: str, amount: int, package_name: str) -> dict:
    """Mock payment execution that commits the transaction to MongoDB."""
    txn_id = f"TXN{uuid.uuid4().hex[:7].upper()}"
    new_record = {
        "user_id": user_id,
        "txn_id": txn_id,
        "amount": amount,
        "package": package_name,
        "date": datetime.now(),
        "status": "SUCCESS"
    }
    await recharge_history_collection.insert_one(new_record)
    return new_record

async def recharge_node(state: AgentState) -> dict:
    slots = state.recharge_slots
    last_user_message = state.messages[-1].content.strip().lower()

    
    #  Human-in-the-Loop Confirmation Handling

    if state.awaiting_recharge_confirmation:
        if any(affirm in last_user_message for affirm in ["yes", "approve", "confirm", "proceed", "y", "sure", "ok"]):
            effective_user = slots.user_id or state.user_id
            record = await perform_recharge(
                user_id=effective_user,
                amount=slots.amount,
                package_name=slots.package_name
            )
            success_response = (
                f"✅ **Recharge Successful!**\n\n"
                f"• **Transaction ID:** `{record['txn_id']}`\n"
                f"• **User ID:** `{record['user_id']}`\n"
                f"• **Package:** {record['package']}\n"
                f"• **Amount Paid:** ₹{record['amount']}\n"
                f"• **Status:** {record['status']}\n\n"
                f"Your channels have been renewed. Thank you for choosing DishTV!"
            )
            return {
                "messages": [AIMessage(content=success_response)],
                "awaiting_recharge_confirmation": False,
                "recharge_slots": RechargeSlots()
            }
        elif any(negate in last_user_message for negate in ["no", "cancel", "stop", "abort", "n"]):
            cancel_response = "❌ The recharge request has been cancelled. Let me know if you need help with anything else!"
            return {
                "messages": [AIMessage(content=cancel_response)],
                "awaiting_recharge_confirmation": False,
                "recharge_slots": RechargeSlots()
            }
        else:
            repeat_msg = (
                f"Please confirm your recharge of **₹{slots.amount}** on **{slots.package_name}**.\n"
                f"Reply with **'Yes'** to approve or **'No'** to cancel."
            )
            return {
                "messages": [AIMessage(content=repeat_msg)],
                "awaiting_recharge_confirmation": True
            }

    
    #  Dynamic Extraction & Live Database Resolution
    
    extractor = llm.with_structured_output(ExtractedRechargeDetails)
    extraction_prompt = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        state.messages[-1]
    ]
    extracted: ExtractedRechargeDetails = await extractor.ainvoke(extraction_prompt)

    amount = extracted.amount or slots.amount
    package_name = extracted.package_name or slots.package_name
    user_id = extracted.user_id or slots.user_id or state.user_id

    # Dynamic Lookup from MongoDB: If package is specified, fetch its live name & price
    if package_name:
        db_pack = await lookup_package_and_price(package_name)
        if db_pack:
            package_name = db_pack["name"]
            if not amount and db_pack["price"]:
                amount = db_pack["price"]

    # Dynamic Lookup from MongoDB: If amount is specified but package is not, find matching pack
    if amount and not package_name:
        all_packs = await get_all_recharge_packages()
        for p in all_packs:
            if p["price"] == amount:
                package_name = p["name"]
                break

    updated_slots = RechargeSlots(
        amount=amount,
        package_name=package_name,
        user_id=user_id,
        is_confirmed=False
    )

    
    #  Slot Filling Checks (Dynamic from Database)
    
    # If neither package nor amount is specified, fetch all active packs from MongoDB and present them!
    if not updated_slots.amount and not updated_slots.package_name:
        active_packs = await get_all_recharge_packages()
        
        pack_lines = []
        for p in active_packs[:4]:  # Top 4 packages from DB
            price_str = f"₹{p['price']}/month" if p['price'] else p['pricing_raw']
            pack_lines.append(f"• **{p['name']}**: {price_str}")

        guidance = (
            "I can help you recharge your DishTV account! Here are the active packages from our catalog:\n\n"
            + "\n".join(pack_lines) +
            "\n\nWhich package would you like to recharge? (You can say e.g. *'Recharge Super Family'* or *'Recharge for 191'*)."
        )
        return {
            "messages": [AIMessage(content=guidance)],
            "recharge_slots": updated_slots,
            "awaiting_recharge_confirmation": False
        }

    # If amount is known but package is still unknown
    if updated_slots.amount and not updated_slots.package_name:
        return {
            "messages": [AIMessage(content=f"Which package would you like to recharge for ₹{updated_slots.amount}? (e.g. Super Family, Flexi HD, Swagat Combo).")],
            "recharge_slots": updated_slots,
            "awaiting_recharge_confirmation": False
        }

    
    #  Human-in-the-Loop Confirmation Gate (Native LangGraph Interrupt)
    # Both package and amount are resolved from MongoDB!
   
    confirmation_prompt = (
        f"You are about to recharge for **₹{updated_slots.amount}** on **{updated_slots.package_name}**.\n\n"
        f"Do you approve? (Yes/No)"
    )

    # Graph pauses right here and returns confirmation_prompt to client
    user_decision = interrupt(confirmation_prompt)

    # Execution resumes right here when user sends 'Yes' / 'No'
    decision_str = str(user_decision).strip().lower()
    if any(affirm in decision_str for affirm in ["yes", "approve", "confirm", "proceed", "y", "sure", "ok"]):
        effective_user = updated_slots.user_id or state.user_id
        record = await perform_recharge(
            user_id=effective_user,
            amount=updated_slots.amount,
            package_name=updated_slots.package_name
        )
        success_response = (
            f"✅ **Recharge Successful!**\n\n"
            f"• **Transaction ID:** `{record['txn_id']}`\n"
            f"• **User ID:** `{record['user_id']}`\n"
            f"• **Package:** {record['package']}\n"
            f"• **Amount Paid:** ₹{record['amount']}\n"
            f"• **Status:** {record['status']}\n\n"
            f"Your channels have been renewed. Thank you for choosing DishTV!"
        )
        return {
            "messages": [AIMessage(content=success_response)],
            "recharge_slots": RechargeSlots()
        }
    else:
        return {
            "messages": [AIMessage(content="❌ The recharge request has been cancelled. Let me know if you need help with anything else!")],
            "recharge_slots": RechargeSlots()
        }
