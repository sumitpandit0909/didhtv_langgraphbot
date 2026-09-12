from app.core.config import settings
from langchain_openrouter import ChatOpenRouter

def get_llm(temperature: float = 0.3):
    return ChatOpenRouter(
        model="nex-agi/nex-n2.5-mini:free",
        api_key=settings.OPENROUTER_API_KEY,
        temperature=temperature,
        max_retries=3
    )