"""
Athena AI — Interview Orchestrator
Manages the full interview session lifecycle:
start → question → answer → evaluate → next question → report
"""
import uuid
from typing import Optional
from loguru import logger

from models.interview import (
    InterviewState, InterviewStatus, CandidateProfile,
    QuestionType, DifficultyLevel, ReasoningTrace,
    StartInterviewRequest, StartInterviewResponse,
    RespondRequest, RespondResponse, FeedbackReport
)
from knowledge.knowledge_graph import KnowledgeGraph
from memory.memory_engine import MemoryEngine
from agents.interview_agents import (
    generate_question, evaluate_answer, plan_next_question
)
from agents.feedback_agent import generate_report
from core.config import settings

# In-memory session store (replace with Redis for production)
_sessions: dict[str, dict] = {}


def _get_session(session_id: str) -> Optional[dict]:
    return _sessions.get(session_id)


def _save_session(session_id: str, state: InterviewState, graph: KnowledgeGraph, memory: MemoryEngine):
    _sessions[session_id] = {
        "state": state,
        "graph": graph,
        "memory": memory,
    }


def _determine_initial_topic(profile: CandidateProfile, graph: KnowledgeGraph) -> str:
    """Pick the best starting topic based on candidate profile."""
    # If candidate has skipped topics, start there
    skipped = profile.skipped_topics
    all_nodes = list(graph.graph.nodes)

    for topic in skipped:
        if topic in all_nodes:
            return topic

    # Otherwise, start with a foundational topic
    # Find nodes with no predecessors (root nodes)
    roots = [n for n in graph.graph.nodes if graph.graph.in_degree(n) == 0]
    if roots:
        return roots[0]

    return "Prompt Engineering"


async def start_interview(request: StartInterviewRequest) -> StartInterviewResponse:
    """Initialize a new interview session."""
    session_id = f"sess_{uuid.uuid4().hex[:12]}"

    # Build candidate profile
    candidate = CandidateProfile(
        candidate_id=request.candidate_id or f"cand_{uuid.uuid4().hex[:8]}",
        name=request.name,
        completed_missions=request.completed_missions,
        skipped_topics=request.skipped_topics,
        curriculum_json=request.curriculum_json,
        learning_signals=request.learning_signals or {},
    )

    # Initialize graph & memory
    graph = KnowledgeGraph()
    memory = MemoryEngine()

    # Pre-populate graph from learning signals
    for topic, confidence in (request.learning_signals or {}).items():
        graph.update_confidence(topic, confidence)

    # Initialize state
    state = InterviewState(
        session_id=session_id,
        candidate=candidate,
        status=InterviewStatus.IN_PROGRESS,
    )

    # Determine first topic
    first_topic = _determine_initial_topic(candidate, graph)

    # Generate first question
    first_question = await generate_question(
        topic=first_topic,
        question_type=QuestionType.THEORY,
        difficulty=DifficultyLevel.EASY,
        candidate_name=candidate.name,
    )

    # Update state
    state.current_question = first_question
    state.current_question_type = QuestionType.THEORY
    state.current_topic = first_topic
    state.current_curriculum_day = graph.get_curriculum_day(first_topic)
    state.current_difficulty = DifficultyLevel.EASY
    state.questions_asked = 1
    state.current_reasoning_trace = ReasoningTrace(
        weak_node=first_topic,
        dependency_path=[first_topic],
        human_explanation=f"Starting with {first_topic} — a core foundation of the AI curriculum.",
    )

    # Save session
    _save_session(session_id, state, graph, memory)

    logger.info(f"🎬 Interview started: {session_id} for {candidate.name}")

    return StartInterviewResponse(
        session_id=session_id,
        candidate_id=candidate.candidate_id,
        status=InterviewStatus.IN_PROGRESS,
        question_number=1,
        question=first_question,
        question_type=QuestionType.THEORY,
        topic=first_topic,
        curriculum_day=state.current_curriculum_day,
        difficulty_level=DifficultyLevel.EASY,
        reasoning_trace=state.current_reasoning_trace,
        total_questions_planned=settings.MIN_QUESTIONS,
    )


async def respond_to_question(request: RespondRequest) -> RespondResponse:
    """Process an answer and return the next question or complete the interview."""
    session = _get_session(request.session_id)
    if not session:
        raise ValueError(f"Session not found: {request.session_id}")

    state: InterviewState = session["state"]
    graph: KnowledgeGraph = session["graph"]
    memory: MemoryEngine = session["memory"]

    # ── Evaluate the answer ──────────────────────────────────
    evaluation = await evaluate_answer(
        question=state.current_question,
        answer=request.answer,
        topic=state.current_topic,
        question_type=state.current_question_type,
        difficulty=state.current_difficulty,
    )

    score = evaluation.get("score", 0.5)
    feedback = evaluation.get("feedback", "")

    # ── Update graph confidence ──────────────────────────────
    graph.update_confidence(state.current_topic, score)

    # ── Update Digital Twin ──────────────────────────────────
    state.topic_confidence[state.current_topic] = score
    state.last_answer = request.answer
    state.last_answer_score = score
    state.last_answer_feedback = feedback
    state.confidence_score = (
        sum(state.topic_confidence.values()) / len(state.topic_confidence)
        if state.topic_confidence else 0.5
    )

    # Consecutive tracking
    if score >= 0.65:
        state.consecutive_correct += 1
        state.consecutive_wrong = 0
    else:
        state.consecutive_wrong += 1
        state.consecutive_correct = 0

    # ── Record in memory ─────────────────────────────────────
    memory.record_qa(
        question=state.current_question,
        answer=request.answer,
        topic=state.current_topic,
        curriculum_day=state.current_curriculum_day,
        question_type=state.current_question_type.value,
        score=score,
    )

    # ── Record in Q&A history ────────────────────────────────
    state.qa_history.append({
        "question_number": state.questions_asked,
        "question": state.current_question,
        "answer": request.answer,
        "topic": state.current_topic,
        "curriculum_day": state.current_curriculum_day,
        "question_type": state.current_question_type.value,
        "difficulty": state.current_difficulty.value,
        "score": score,
        "feedback": feedback,
    })

    if state.current_topic not in state.topics_covered:
        state.topics_covered.append(state.current_topic)
    if state.current_curriculum_day and state.current_curriculum_day not in state.curriculum_days_covered:
        state.curriculum_days_covered.append(state.current_curriculum_day)

    # ── Check if interview is complete ───────────────────────
    is_complete = (
        state.questions_asked >= settings.MIN_QUESTIONS
        and len(state.curriculum_days_covered) >= settings.MIN_CURRICULUM_DAYS
        and state.questions_asked >= settings.MIN_QUESTIONS
    )

    if state.questions_asked >= settings.MAX_QUESTIONS:
        is_complete = True

    if is_complete:
        state.status = InterviewStatus.COMPLETE
        _save_session(request.session_id, state, graph, memory)
        logger.info(f"✅ Interview complete: {request.session_id} ({state.questions_asked} questions)")
        return RespondResponse(
            session_id=request.session_id,
            question_number=state.questions_asked,
            answer_score=score,
            answer_feedback=feedback,
            interview_complete=True,
            questions_remaining=0,
            message="Interview complete! Generating your report... 🦉",
        )

    # ── Plan next question ───────────────────────────────────
    weak_topics = [
        t for t, c in graph.get_all_scores().items()
        if c < 0.65 and t not in state.topics_covered[-2:]
    ]

    plan = await plan_next_question(
        topic=state.current_topic,
        weak_topics=weak_topics,
        topics_covered=state.topics_covered,
        days_covered=state.curriculum_days_covered,
        confidence_score=state.confidence_score,
        consecutive_correct=state.consecutive_correct,
        consecutive_wrong=state.consecutive_wrong,
        recent_context=memory.get_context_for_llm(),
        questions_asked=state.questions_asked,
        min_questions=settings.MIN_QUESTIONS,
        min_days=settings.MIN_CURRICULUM_DAYS,
    )

    next_topic = plan.get("next_topic", state.current_topic)
    next_type_str = plan.get("question_type", "theory")
    next_difficulty_int = plan.get("difficulty", 2)

    try:
        next_type = QuestionType(next_type_str)
    except ValueError:
        next_type = QuestionType.THEORY

    try:
        next_difficulty = DifficultyLevel(min(max(int(next_difficulty_int), 1), 7))
    except ValueError:
        next_difficulty = DifficultyLevel.MEDIUM

    # ── Generate next question ───────────────────────────────
    next_question = await generate_question(
        topic=next_topic,
        question_type=next_type,
        difficulty=next_difficulty,
        context=memory.get_context_for_llm(),
        last_answer=request.answer if next_type == QuestionType.FOLLOW_UP else "",
        candidate_name=state.candidate.name,
    )

    # ── Build reasoning trace ────────────────────────────────
    dep_path = graph.get_dependency_path(next_topic)
    reasoning_trace = ReasoningTrace(
        weak_node=next_topic if next_topic in weak_topics else None,
        dependency_path=dep_path,
        proposing_agent="Chief Interview Agent",
        chief_rationale=plan.get("rationale", ""),
        human_explanation=plan.get("human_explanation", f"Exploring your knowledge of {next_topic}."),
    )

    # ── Update state for next question ───────────────────────
    state.questions_asked += 1
    state.current_question = next_question
    state.current_question_type = next_type
    state.current_topic = next_topic
    state.current_curriculum_day = graph.get_curriculum_day(next_topic)
    state.current_difficulty = next_difficulty
    state.current_reasoning_trace = reasoning_trace

    _save_session(request.session_id, state, graph, memory)

    questions_remaining = max(0, settings.MIN_QUESTIONS - state.questions_asked)

    return RespondResponse(
        session_id=request.session_id,
        question_number=state.questions_asked,
        question=next_question,
        question_type=next_type,
        topic=next_topic,
        curriculum_day=state.current_curriculum_day,
        difficulty_level=next_difficulty,
        reasoning_trace=reasoning_trace,
        answer_score=score,
        answer_feedback=feedback,
        interview_complete=False,
        questions_remaining=questions_remaining,
        message=f"Question {state.questions_asked} of {settings.MIN_QUESTIONS}+",
    )


async def get_report(session_id: str) -> FeedbackReport:
    """Generate and return the final interview report."""
    session = _get_session(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    state: InterviewState = session["state"]

    if state.status != InterviewStatus.COMPLETE and state.questions_asked < 3:
        raise ValueError("Interview not complete yet. Please finish the interview first.")

    report = await generate_report(state)
    return report
