"""
Athena AI — FastAPI Application Entry Point
"""
import uuid
import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from api.routes import interview, health, voice, analytics
from core.config import settings
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🦉 Athena AI starting up...")
    await init_db()
    logger.info("✅ Database initialized")
    logger.info(f"🤖 Gemini Provider: {'configured' if settings.GEMINI_API_KEY else 'NOT SET (set GEMINI_API_KEY)'}")
    logger.info(f"🧠 BREATH Memory: {'configured' if settings.BREETH_API_KEY else 'mock mode (set BREETH_API_KEY)'}")
    logger.info(f"🎙️ Voice: {'configured' if settings.VOICE_API_KEY else 'mock mode (set VOICE_API_KEY)'}")
    yield
    logger.info("🦉 Athena AI shutting down...")


app = FastAPI(
    title="Athena AI — Interview Intelligence Platform",
    description=(
        "Autonomous AI interview agent with multi-agent debate, knowledge graphs, "
        "multilingual support, recruiter intelligence, and explainable AI"
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Phase 16: Security Middleware ───────────────────────────────────────────

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers and request tracing to every response."""
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    response: Response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # Security headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    if elapsed_ms > 5000:
        logger.warning(f"⚠️ Slow request [{request_id}]: {request.method} {request.url.path} took {elapsed_ms}ms")

    return response

# ─────────────────────────────────────────────────────────────────────────────

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
app.include_router(voice.router, prefix="/api/v1", tags=["Voice"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])


@app.get("/")
async def root():
    return {
        "name": "Athena AI",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "features": [
            "Multi-domain adaptive interviews",
            "Socratic AI follow-ups",
            "Multilingual support",
            "Resume & JD intelligence",
            "Recruiter intelligence reports",
            "Voice I/O",
            "Real-time analytics",
        ],
    }
