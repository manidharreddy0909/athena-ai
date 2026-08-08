"""
Athena AI — Application Settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Athena AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ----------------------------------------------------------
    # Core external providers required for full architecture
    # ----------------------------------------------------------
    GEMINI_API_KEY: str = ""
    BREETH_API_KEY: str = ""
    BREETH_BASE_URL: str = "https://api.breeth.ai/v1"
    VOICE_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://athena:athena_secret@localhost:5432/athena_db"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Interview
    MIN_QUESTIONS: int = 8
    MIN_CURRICULUM_DAYS: int = 4
    MAX_QUESTIONS: int = 15
    SESSION_TIMEOUT_MINUTES: int = 60

    # LLM retry behavior
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_DELAY_SECONDS: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
