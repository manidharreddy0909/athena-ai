"""
Athena AI — Application Settings
Provider-agnostic: works with OpenRouter, LM Studio, Groq, OpenAI
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Athena AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # LLM (OpenAI-compatible — swap base_url to change provider)
    LLM_BASE_URL: str = "http://localhost:1234/v1"
    LLM_API_KEY: str = "lm-studio"
    LLM_MODEL: str = "gemma-4"

    # Embeddings
    EMBEDDING_BASE_URL: str = "http://localhost:1234/v1"
    EMBEDDING_API_KEY: str = "lm-studio"
    EMBEDDING_MODEL: str = "text-embedding-nomic-embed-text-v1.5"

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
