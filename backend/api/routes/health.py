"""
Athena AI — Health Check Route
"""
from fastapi import APIRouter
from core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_BASE_URL,
        "model": settings.LLM_MODEL,
    }
