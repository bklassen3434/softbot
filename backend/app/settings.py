from pydantic import BaseSettings, AnyUrl
from typing import Optional, List

class Settings(BaseSettings):
    # --- Core
    DATABASE_URL: str

    # --- LLM
    LLM_BASE_URL: str
    LLM_API_KEY: Optional[str] = None  # your provider key
    LLM_MODEL_NAME: str

    # --- Rate limits
    LLM_RATE_MAX: int = 30
    LLM_RATE_WINDOW_SEC: int = 3600  # 1 hour

    # --- SQL Validation
    MAX_LIMIT: int = 500
    DEFAULT_LIMIT: int = 100

    class Config:
        env_file = ".env"  # loaded in local dev; in Docker we inject envs

settings = Settings()
