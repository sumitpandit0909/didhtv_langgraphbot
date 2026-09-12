# app/nodes/techchefz_rag.py
import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from flashrank import Ranker, RerankRequest

from app.core.config import settings
from app.models import AgentState
from app.core.llm import get_llm

llm = get_llm()
embeddings = GoogleGenerativeAIEmbeddings(
    google_api_key=settings.GEMINI_API_KEY,
    model="gemini-embedding-001"
)

#  Vector Store 
persist_dir = os.path.join("app", "database", "chroma_db")
vectorstore = Chroma(
    persist_directory=persist_dir,
    collection_name="techchefz_knowledge",
    embedding_function=embeddings
)
# fetch 8 candidates and then we will rerank it to top 3
retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

# Reranker 
ranker = Ranker(model_name="ms-marco-TinyBERT-L-2-v2", cache_dir="/tmp/flashrank")

# Confidence / Relevance Evaluator Schema 
class RelevanceGrade(BaseModel):
    is_relevant: Literal["yes", "no"] = Field(
        ...,
        description="Whether the retrieved context contains relevant information to answer the user's query."
    )
    confidence_score: float = Field(
        ...,
        description="Confidence score from 0.0 to 1.0 indicating how well the context covers the question."
    )

GRADER_SYSTEM_PROMPT = """You are a document relevance evaluator for TechChefz Digital.
Check if the retrieved documents contain sufficient, relevant information to answer the user query.
If the query is completely unrelated to TechChefz, its services, team, or offerings, or if the documents lack the answer, respond with 'no'.
"""

grader_prompt = ChatPromptTemplate.from_messages([
    ("system", GRADER_SYSTEM_PROMPT),
    ("human", "User Query: {query}\n\nRetrieved Documents:\n{context}")
])

# Query Transformation Prompt
QUERY_TRANSFORMATION_SYSTEM = """Given chat history and the latest user query, reformulate it into a standalone search query about TechChefz Digital.
Do NOT answer the question. Only output the standalone search string.
"""

query_transform_prompt = ChatPromptTemplate.from_messages([
    ("system", QUERY_TRANSFORMATION_SYSTEM),
    MessagesPlaceholder(variable_name="messages"),
])

# Final Generation Prompt
RAG_SYSTEM_PROMPT = """You are DishBot, representing TechChefz Digital.
Answer the user's question accurately using ONLY the provided verified context below.
Keep your response professional, concise, and well-structured with bullet points where appropriate.

Context:
{context}
"""

rag_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

async def techchefz_rag_node(state: AgentState) -> dict:
    """
    Production-Grade RAG Pipeline:
    1. Query Transformation (Multi-turn context condensation).
    2. Dense Vector Retrieval (Top 8 candidate chunks).
    3. Cross-Encoder Reranking (FlashRank down to Top 3).
    4. Confidence / Relevance Gate (Prevents hallucinating on missing facts).
    5. Grounded Generation with Official Citation.
    """
    # Query Transformation
    if len(state.messages) > 1:
        transform_chain = query_transform_prompt | llm
        transform_res = await transform_chain.ainvoke({"messages": state.messages})
        search_query = transform_res.content.strip()
    else:
        search_query = state.messages[-1].content.strip()

    # Candidate Retrieval (Top 8)
    candidates = await retriever.ainvoke(search_query)

    # Cross-Encoder Reranking (Top 8 -> Top 3)
    if candidates:
        passages = [{"id": i, "text": doc.page_content} for i, doc in enumerate(candidates)]
        rerank_req = RerankRequest(query=search_query, passages=passages)
        reranked_results = ranker.rerank(rerank_req)[:3]
        
        top_chunks = [res["text"] for res in reranked_results]
        context_text = "\n\n---\n\n".join([f"[Doc {i+1}]: {text}" for i, text in enumerate(top_chunks)])
    else:
        context_text = ""

    #Confidence & Relevance Grading Loop
    grader_chain = grader_prompt | llm.with_structured_output(RelevanceGrade)
    grade: RelevanceGrade = await grader_chain.ainvoke({
        "query": search_query,
        "context": context_text or "No documents found."
    })

    source_url = "https://www.techchefz.digital"

    # If context is not relevant or confidence is low, trigger fallback
    if grade.is_relevant == "no" or grade.confidence_score < 0.4 or not context_text:
        fallback_msg = (
            "I apologize, but I couldn't find verified information about that specific query in TechChefz's documentation. "
            "You can learn more directly at [TechChefz Digital](https://www.techchefz.digital) or contact our sales team at sales@techchefz.com."
        )
        return {
            "messages": [AIMessage(content=fallback_msg)],
            "source_url": source_url
        }

    # Grounded Answer Synthesis
    gen_chain = rag_generation_prompt | llm
    ai_response = await gen_chain.ainvoke({
        "context": context_text,
        "messages": state.messages
    })

    final_content = f"{ai_response.content}\n\n**Source:** [TechChefz Digital]({source_url})"

    return {
        "messages": [AIMessage(content=final_content)],
        "source_url": source_url
    }
