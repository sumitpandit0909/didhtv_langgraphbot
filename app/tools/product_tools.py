import re
from typing import Optional, List ,Dict,Any
from langchain_core.tools import tool

from app.database.connection import products_collection


@tool
async def search_product(query:str)-> List[Dict[str,Any]]:
    """
    Search for a specific DishTV product, set-top box, or package in MongoDB by keyword or name.
    Use this when the user asks about features, pricing, or specifications of a particular item.
    """
    if isinstance(query, list):
        query = " ".join(str(q) for q in query)
    elif not isinstance(query, str):
        query = str(query)
    regex_pattern =re.compile(re.escape(query.strip()),re.IGNORECASE)

    cursor = products_collection.find({
        "$or":[
            {"product_name":{"$regex":regex_pattern}},
            {"description":{"$regex":regex_pattern}},
            {"category":{"$regex":regex_pattern}}
        ]
    })

    results = await cursor.to_list(length=5)

    #remove objectid from resultj

    clean_results = []
    for doc in results:
        clean_results.append({
            "product_name": doc.get("product_name"),
            "description": doc.get("description"),
            "features": doc.get("features", []),
            "pricing": doc.get("pricing", "Contact support"),
            "source_url": doc.get("source_url", "https://www.dishtv.in"),
            "category": doc.get("category", "")
        })
    
    return clean_results


@tool
async def list_all_products(category:Optional[str]=None)->List[Dict[str,Any]]:
    """
    List all available DishTV products, set-top boxes, and packages from MongoDB.
    Use this when the user asks 'What products do you have?', 'Show me all packs', or 'List your set-top boxes'.
    Optional category: 'hardware' or 'package'.
    """
    filter_query={}
    if category:
        filter_query["category"] =category.lower()

    cursor = products_collection.find(filter_query)
    results = await cursor.to_list(length=100)

    items = []
    for doc in results:
        items.append({
            "product_name": doc.get("product_name"),
            "category": doc.get("category"),
            "pricing": doc.get("pricing"),
            "source_url": doc.get("source_url")
        })
    return items
    
