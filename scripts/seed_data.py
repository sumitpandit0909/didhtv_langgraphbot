# scripts/seed_data.py
import json 
import os
import asyncio
from datetime import datetime
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.database.connection import products_collection, recharge_history_collection
from app.core.config import settings

async def seed_dishtv_products():
    json_path = os.path.join("app", "database", "dishtv_data.json")
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    await products_collection.delete_many({})
    docs_to_insert = []

    # 1. Products (Set-Top Boxes, Remotes, TVs)
    for item in data.get("products", []):
        docs_to_insert.append({
            "product_name": item.get("productname", "").strip(),
            "description": item.get("descriptoin", "").strip(),
            "features": item.get("feautures", []),
            "pricing": item.get("pricing", ""),
            "source_url": item.get("sourceurl", "https://www.dishtv.in"),
            "category": "hardware"
        })

    # 2. Recharge Packages
    for item in data.get("packages_and_recharges", []):
        docs_to_insert.append({
            "product_name": item.get("packname", "").strip(),  # Note: packname in JSON
            "description": item.get("descriptoin", "").strip(),
            "features": item.get("feautures", []),
            "pricing": item.get("pricing", ""),
            "source_url": item.get("sourceurl", "https://www.dishtv.in"),
            "category": "package"
        })

    if docs_to_insert:
        await products_collection.insert_many(docs_to_insert)
        print(f" [1/3] Seeded {len(docs_to_insert)} DishTV products & packages into MongoDB.")

async def seed_recharge_history():
    await recharge_history_collection.delete_many({})
    
    dummy_history = [
        {
            "user_id": "user_123",
            "txn_id": "TXN98231",
            "amount": 249,
            "package": "Super Family (Flexi Pack 249)",
            "date": datetime(2026, 1, 10, 14, 30),
            "status": "SUCCESS"
        },
        {
            "user_id": "user_123",
            "txn_id": "TXN98542",
            "amount": 191,
            "package": "Flexi HD Pack",
            "date": datetime(2026, 2, 8, 18, 15),
            "status": "SUCCESS"
        },
        {
            "user_id": "user_123",
            "txn_id": "TXN99104",
            "amount": 249,
            "package": "Super Family (Flexi Pack 249)",
            "date": datetime(2026, 3, 5, 11, 45),
            "status": "SUCCESS"
        }
    ]
    await recharge_history_collection.insert_many(dummy_history)
    print(" [2/3] Seeded 3 dummy recharge records for 'user_123'.")

def ingest_techchef_data():
    pdf_path = "TechChefz Digital __ Chatbot Content.docx.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found")
        return

    print(" Reading TechChefz Digital PDF content...")
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = splitter.split_text(full_text)

    # Initialize Google Gemini Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        google_api_key=settings.GEMINI_API_KEY,
        model="gemini-embedding-001"  # or "models/text-embedding-004"
    )
    
    persist_dir = os.path.join("app", "database", "chroma_db")
    Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="techchefz_knowledge"
    )
    print(f" [3/3] Ingested {len(chunks)} chunks into ChromaDB at '{persist_dir}'.")

async def main():
    await seed_dishtv_products()
    await seed_recharge_history()
    ingest_techchef_data()
    print(" All Data Ingestion Complete!")

if __name__ == "__main__":
    asyncio.run(main())
