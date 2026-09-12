from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    OPENROUTER_API_KEY: str 
    OPENAI_API_KEY: str 
    MONGODB_URI: str 
    MONGODB_DB_NAME :str
    LANGCHAIN_TRACING_V2: str 
    LANGCHAIN_API_KEY: str 
    LANGCHAIN_PROJECT: str 
    GEMINI_API_KEY :str

    model_config =SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()