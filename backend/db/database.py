"""
Athena AI — Database Setup (SQLAlchemy Async)
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, Text
from datetime import datetime
from core.config import settings
from loguru import logger


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    session_id = Column(String, primary_key=True)
    candidate_id = Column(String, nullable=False)
    candidate_name = Column(String, nullable=False)
    status = Column(String, default="in_progress")
    state_json = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_questions = Column(Integer, default=0)
    overall_score = Column(Float, nullable=True)
    report_json = Column(JSON, nullable=True)


class QuestionRecord(Base):
    __tablename__ = "question_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    curriculum_day = Column(Integer, nullable=True)
    difficulty_level = Column(Integer, default=1)
    reasoning_trace_json = Column(JSON, nullable=True)
    answer_text = Column(Text, nullable=True)
    answer_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    """Create all tables on startup."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.warning(f"⚠️ Database not available (running without DB): {e}")


async def get_db():
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session
