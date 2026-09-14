# app/main.py
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.core.config import settings
from app.models import ChatRequest, ChatResponse
from app.graph import dishbot_graph
from app.database.connection import chats_collection

# 1. Ensure LangSmith Tracing environment variables are actively exported
if settings.LANGCHAIN_TRACING_V2:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
if settings.LANGCHAIN_PROJECT:
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

# 2. Initialize FastAPI
app = FastAPI(
    title="DishBot - Agentic Support System for DishTV",
    description="Router-based Conversational Agent built with LangGraph, FastAPI, and MongoDB",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "DishBot Agentic System"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint as specified in Assignment Section 4.D:
    Input: {"message": "str", "user_id": "str", "conversation_id": "str"}
    Output: {"response": "str", "source": "str (optional)", "status": "success"}
    """
    try:
        # 1. Configure LangGraph thread using conversation_id for multi-turn session memory
        config = {
            "configurable": {
                "thread_id": request.conversation_id
            }
        }

        # 2. Check if graph is currently paused on an interrupt
        current_state = await dishbot_graph.aget_state(config)

        if current_state.next:
            # Graph is paused at an interrupt (e.g. recharge confirmation) -> Resume execution with user response!
            output_state = await dishbot_graph.ainvoke(
                Command(resume=request.message),
                config=config
            )
        else:
            # Normal conversation turn
            input_state = {
                "messages": [HumanMessage(content=request.message)],
                "user_id": request.user_id,
                "conversation_id": request.conversation_id
            }
            output_state = await dishbot_graph.ainvoke(input_state, config=config)

        # 3. Check if this step paused at a new interrupt
        new_state = await dishbot_graph.aget_state(config)
        source_url = None

        if new_state.tasks and new_state.tasks[0].interrupts:
            # Interrupted (e.g. waiting for recharge approval) -> return interrupt prompt
            interrupt_val = new_state.tasks[0].interrupts[0].value
            bot_response = str(interrupt_val)
        else:
            raw_response = output_state["messages"][-1].content
            if isinstance(raw_response, list):
                bot_response = "\n".join([p.get("text", str(p)) if isinstance(p, dict) else str(p) for p in raw_response])
            else:
                bot_response = str(raw_response)
            if isinstance(output_state, dict):
                source_url = output_state.get("source_url")

        # 4. Persist interaction into MongoDB 'chats_collection'
        chat_log = {
            "conversation_id": request.conversation_id,
            "user_id": request.user_id,
            "user_message": request.message,
            "bot_response": bot_response,
            "source": source_url,
            "timestamp": datetime.now()
        }
        await chats_collection.insert_one(chat_log)

        # 5. Return response matching assignment schema
        return ChatResponse(
            response=bot_response,
            source=source_url,
            status="success"
        )

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )
