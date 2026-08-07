"""
Athena AI — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from api.routes import interview, health
from core.config import settings
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🦉 Athena AI starting up...")
    await init_db()
    logger.info("✅ Database initialized")
    logger.info(f"🤖 LLM Provider: {settings.LLM_BASE_URL}")
    logger.info(f"🗺️  Model: {settings.LLM_MODEL}")
    yield
    logger.info("🦉 Athena AI shutting down...")


app = FastAPI(
    title="Athena AI — Interview Intelligence Platform",
    description="Autonomous AI interview agent with multi-agent debate, knowledge graphs, and explainable AI",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(interview.router, prefix="/api/v1", tags=["Interview"])


@app.get("/")
async def root():
    return {
        "name": "Athena AI",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }
