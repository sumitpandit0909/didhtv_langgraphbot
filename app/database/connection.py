from pymongo import AsyncMongoClient
from app.core.config import settings


client = AsyncMongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]

products_collection = db["products_collection"]
recharge_history_collection = db["recharge_history_collection"]
chats_collection = db["chats_collection"]