"""
Athena AI — Pydantic Models: Candidate & Interview
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class QuestionType(str, Enum):
    THEORY = "theory"
    CODING = "coding"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    SYSTEM_DESIGN = "system_design"
    OPTIMIZATION = "optimization"
    EDGE_CASE = "edge_case"
    FOLLOW_UP = "follow_up"


class DifficultyLevel(int, Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    EXPERT = 4
    RESEARCH = 5
    SYSTEM_DESIGN = 6
    PRODUCTION_SCALE = 7


class InterviewStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ERROR = "error"


class HiringRecommendation(str, Enum):
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    CONSIDER = "consider"
    NO_HIRE = "no_hire"


# ─────────────────────────────────────────────
# Candidate Models
# ─────────────────────────────────────────────

class CandidateProfile(BaseModel):
    candidate_id: str = Field(default_factory=lambda: f"cand_{uuid.uuid4().hex[:8]}")
    name: str
    completed_missions: List[int] = Field(default_factory=list, description="Curriculum day numbers completed")
    skipped_topics: List[str] = Field(default_factory=list)
    attempts: Dict[str, int] = Field(default_factory=dict, description="Topic -> attempt count")
    learning_signals: Dict[str, float] = Field(default_factory=dict, description="Topic -> confidence 0-1")
    curriculum_json: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────
# Reasoning & Explainability
# ─────────────────────────────────────────────

class ReasoningTrace(BaseModel):
    weak_node: Optional[str] = None
    dependency_path: List[str] = Field(default_factory=list)
    proposing_agent: Optional[str] = None
    chief_rationale: Optional[str] = None
    human_explanation: str = ""
    difficulty_rationale: Optional[str] = None


# ─────────────────────────────────────────────
# Interview API Models
# ─────────────────────────────────────────────

class StartInterviewRequest(BaseModel):
    candidate_id: Optional[str] = None
    name: str = Field(..., description="Candidate full name")
    completed_missions: List[int] = Field(default_factory=list)
    skipped_topics: List[str] = Field(default_factory=list)
    curriculum_json: Optional[Dict[str, Any]] = None
    learning_signals: Optional[Dict[str, float]] = None


class StartInterviewResponse(BaseModel):
    session_id: str
    candidate_id: str
    status: InterviewStatus = InterviewStatus.IN_PROGRESS
    question_number: int = 1
    question: str
    question_type: QuestionType
    topic: str
    curriculum_day: Optional[int] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.EASY
    reasoning_trace: ReasoningTrace
    total_questions_planned: int
    message: str = "Interview started. Good luck! 🦉"


class RespondRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from start response")
    answer: str = Field(..., description="Candidate's answer text")


class RespondResponse(BaseModel):
    session_id: str
    question_number: int
    question: Optional[str] = None
    question_type: Optional[QuestionType] = None
    topic: Optional[str] = None
    curriculum_day: Optional[int] = None
    difficulty_level: Optional[DifficultyLevel] = None
    reasoning_trace: Optional[ReasoningTrace] = None
    answer_score: Optional[float] = None
    answer_feedback: Optional[str] = None
    interview_complete: bool = False
    questions_remaining: int = 0
    message: str = ""


# ─────────────────────────────────────────────
# Scoring & Feedback
# ─────────────────────────────────────────────

class DimensionScore(BaseModel):
    score: float = Field(ge=0, le=100)
    percentile: Optional[str] = None
    notes: str = ""


class FeedbackReport(BaseModel):
    session_id: str
    candidate_id: str
    candidate_name: str
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: Optional[float] = None

    # Dimension scores
    overall_score: float = Field(ge=0, le=100)
    technical_depth: DimensionScore
    coding_ability: DimensionScore
    architecture: DimensionScore
    communication: DimensionScore
    reasoning: DimensionScore
    hiring_confidence: str = "medium"

    # Recommendation
    hiring_recommendation: HiringRecommendation

    # Details
    strong_areas: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    topics_covered: List[str] = Field(default_factory=list)
    curriculum_days_covered: List[int] = Field(default_factory=list)
    total_questions: int = 0

    # Knowledge Graph snapshot
    knowledge_graph_snapshot: Dict[str, float] = Field(
        default_factory=dict,
        description="topic -> confidence score"
    )

    # Learning plan
    learning_plan_30_day: List[str] = Field(default_factory=list)
    learning_plan_60_day: List[str] = Field(default_factory=list)
    learning_plan_90_day: List[str] = Field(default_factory=list)

    # Q&A transcript
    qa_transcript: List[Dict[str, Any]] = Field(default_factory=list)


# ─────────────────────────────────────────────
# Interview State (Internal LangGraph State)
# ─────────────────────────────────────────────

class InterviewState(BaseModel):
    """Full state of the interview — passed through LangGraph nodes."""
    session_id: str
    candidate: CandidateProfile
    status: InterviewStatus = InterviewStatus.IN_PROGRESS
    started_at: datetime = Field(default_factory=datetime.utcnow)

    # Progress
    questions_asked: int = 0
    current_question: Optional[str] = None
    current_question_type: Optional[QuestionType] = None
    current_topic: Optional[str] = None
    current_curriculum_day: Optional[int] = None
    current_difficulty: DifficultyLevel = DifficultyLevel.EASY
    current_reasoning_trace: Optional[ReasoningTrace] = None

    # History
    qa_history: List[Dict[str, Any]] = Field(default_factory=list)
    topics_covered: List[str] = Field(default_factory=list)
    curriculum_days_covered: List[int] = Field(default_factory=list)

    # Digital Twin (live scores)
    skill_scores: Dict[str, float] = Field(default_factory=dict)
    topic_confidence: Dict[str, float] = Field(default_factory=dict)
    confidence_score: float = 0.5
    consecutive_correct: int = 0
    consecutive_wrong: int = 0

    # Last answer
    last_answer: Optional[str] = None
    last_answer_score: Optional[float] = None
    last_answer_feedback: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
