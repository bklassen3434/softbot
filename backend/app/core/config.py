from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "softball-chatbot"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    MODEL_NAME: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 512

    REDIS_URL: str = "redis://redis:6379"
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/softball_db"

    model_config = {
        "env_file": ".env"
    }

settings = Settings()
