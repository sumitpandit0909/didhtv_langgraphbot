from app.core.config import settings
from langchain_openrouter import ChatOpenRouter

def get_llm(temperature: float = 0.3):
    return ChatOpenRouter(
        model="deepseek/deepseek-v4-flash-0731",
        api_key=settings.OPENROUTER_API_KEY,
        temperature=temperature
    )