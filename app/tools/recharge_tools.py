import re
from typing import List, Dict, Any, Optional
from app.database.connection import products_collection

def extract_price_from_text(pricing_text: str) -> Optional[int]:
    """Extracts the first numeric rupee value from pricing string like '₹249/month'."""
    if not pricing_text:
        return None
    numbers = re.findall(r'\d+', pricing_text)
    return int(numbers[0]) if numbers else None

async def get_all_recharge_packages() -> List[Dict[str, Any]]:
    """
    Fetches all active recharge packages directly from MongoDB products_collection.
    """
    cursor = products_collection.find({"category": "package"})
    docs = await cursor.to_list(length=50)
    
    packages = []
    for doc in docs:
        price = extract_price_from_text(doc.get("pricing", ""))
        packages.append({
            "name": doc.get("product_name"),
            "price": price,
            "description": doc.get("description", ""),
            "pricing_raw": doc.get("pricing", "Contact support"),
            "source_url": doc.get("source_url")
        })
    return packages

async def lookup_package_and_price(query: str) -> Optional[Dict[str, Any]]:
    """
    Searches MongoDB products_collection to match a package name or query,
    returning its official name and price dynamically.
    """
    if not query:
        return None
        
    regex_pattern = re.compile(re.escape(query.strip()), re.IGNORECASE)
    doc = await products_collection.find_one({
        "category": "package",
        "product_name": {"$regex": regex_pattern}
    })
    
    # Fallback: search in description
    if not doc:
        doc = await products_collection.find_one({
            "category": "package",
            "description": {"$regex": regex_pattern}
        })
        
    if doc:
        return {
            "name": doc.get("product_name"),
            "price": extract_price_from_text(doc.get("pricing", "")),
            "pricing_raw": doc.get("pricing")
        }
    return None
