"""
Athena AI — Robust LangGraph Interview State Machine
Implements the exact state transition flow:
INIT → PROFILE_ANALYSIS → QUESTION → ANSWER → EVALUATION → MEMORY_UPDATE → NEXT_QUESTION → REPORT
"""
from typing import Dict, Any, Optional
from loguru import logger
import uuid

from langgraph.graph import StateGraph, END

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
from agents.socratic_engine import should_follow_up, generate_socratic_followup, deep_evaluate_answer
from agents.feedback_agent import generate_report
from core.config import settings

# In-memory storage for state objects
_sessions: Dict[str, Dict[str, Any]] = {}

# ─────────────────────────────────────────────
# LangGraph Nodes
# ─────────────────────────────────────────────

async def node_profile_analysis(state: InterviewState) -> InterviewState:
    """Analyze the candidate profile and select the initial topic."""
    logger.info(f"[{state.session_id}] Executing PROFILE_ANALYSIS")
    
    # Pre-populate knowledge graph with candidate's learning signals
    graph = KnowledgeGraph()
    for topic, confidence in state.candidate.learning_signals.items():
        graph.update_confidence(topic, confidence)
    
    # Pick first topic based on skipped topics or core foundations
    skipped = state.candidate.skipped_topics
    all_nodes = list(graph.graph.nodes)
    
    first_topic = "Prompt Engineering"
    for t in skipped:
        if t in all_nodes:
            first_topic = t
            break
            
    state.current_topic = first_topic
    state.current_curriculum_day = graph.get_curriculum_day(first_topic)
    
    # Build initial Explainable AI reasoning trace from the actual profile decision
    if first_topic in skipped:
        initial_explanation = (
            f"We're starting with {first_topic} because you marked it as skipped — "
            "let's verify your understanding of this topic."
        )
    else:
        initial_explanation = (
            f"We're starting with {first_topic} as a foundational concept "
            "to establish your baseline knowledge."
        )
    state.current_reasoning_trace = ReasoningTrace(
        weak_node=first_topic if first_topic in skipped else None,
        dependency_path=graph.get_dependency_path(first_topic),
        proposing_agent="profile_analyzer",
        chief_rationale="Initial topic selected from candidate profile and curriculum prerequisites.",
        human_explanation=initial_explanation,
        difficulty_rationale="Starting at moderate difficulty to gauge the candidate's baseline.",
    )
    
    # Store instances in global memory for this session
    _sessions[state.session_id]["graph"] = graph
    _sessions[state.session_id]["memory"] = MemoryEngine(session_id=state.session_id)
    
    return state


async def node_generate_question(state: InterviewState) -> InterviewState:
    """Generate the actual question text using LLM."""
    logger.info(f"[{state.session_id}] Executing QUESTION generation")
    
    memory = _sessions[state.session_id]["memory"]
    
    # Ensure a valid question type is set on state (defaults to theory for the first question)
    if state.current_question_type is None:
        state.current_question_type = QuestionType.THEORY
    
    context = await memory.get_context_for_llm(current_topic=state.current_topic)
    
    question = await generate_question(
        topic=state.current_topic or "AI Foundations",
        question_type=state.current_question_type,
        difficulty=state.current_difficulty,
        context=context,
        last_answer=state.last_answer,
        candidate_name=state.candidate.name,
    )
    
    state.current_question = question
    
    if state.questions_asked == 0:
        state.questions_asked = 1 # Initial start
        
    return state


async def node_evaluate_answer(state: InterviewState) -> InterviewState:
    """Evaluate candidate answer with rich dimensional scoring."""
    logger.info(f"[{state.session_id}] Executing EVALUATION")
    
    if not state.last_answer:
        return state

    # Phase 5: Use deep evaluation for rich feedback
    evaluation = await deep_evaluate_answer(
        question=state.current_question or "",
        answer=state.last_answer,
        topic=state.current_topic or "",
        question_type=state.current_question_type or QuestionType.THEORY,
        difficulty=state.current_difficulty,
    )
    
    state.last_answer_score = evaluation.get("score", 0.5)
    state.last_answer_feedback = evaluation.get("feedback", "")
    state.last_strong_points = evaluation.get("strong_points", [])
    state.last_key_gaps = evaluation.get("key_gaps", [])
    return state


async def node_memory_update(state: InterviewState) -> InterviewState:
    """Update Digital Twin, Knowledge Graph, and Memory Engine."""
    logger.info(f"[{state.session_id}] Executing MEMORY_UPDATE")
    
    graph: KnowledgeGraph = _sessions[state.session_id]["graph"]
    memory: MemoryEngine = _sessions[state.session_id]["memory"]
    
    score = state.last_answer_score or 0.5
    topic = state.current_topic or "Unknown"
    
    # Update knowledge graph & twin
    graph.update_confidence(topic, score)
    state.topic_confidence[topic] = score
    
    if score >= 0.65:
        state.consecutive_correct += 1
        state.consecutive_wrong = 0
    else:
        state.consecutive_wrong += 1
        state.consecutive_correct = 0
        
    # Update Memory
    await memory.record_qa(
        question=state.current_question or "",
        answer=state.last_answer or "",
        topic=topic,
        curriculum_day=state.current_curriculum_day,
        question_type=state.current_question_type.value if state.current_question_type else "theory",
        score=score,
    )
    
    # Record History
    state.qa_history.append({
        "question_number": state.questions_asked,
        "question": state.current_question,
        "answer": state.last_answer,
        "topic": topic,
        "curriculum_day": state.current_curriculum_day,
        "score": score,
        "feedback": state.last_answer_feedback,
    })
    
    if topic not in state.topics_covered:
        state.topics_covered.append(topic)
    if state.current_curriculum_day and state.current_curriculum_day not in state.curriculum_days_covered:
        state.curriculum_days_covered.append(state.current_curriculum_day)
        
    return state


async def node_plan_next(state: InterviewState) -> InterviewState:
    """Decide if interview is over, or plan the next topic."""
    logger.info(f"[{state.session_id}] Executing NEXT_QUESTION planning")
    
    # ── Phase 5: Socratic Follow-up Decision ─────────────────────────────
    last_score = state.last_answer_score or 0.5
    last_answer_text = state.last_answer or ""
    do_followup, followup_reason = await should_follow_up(
        score=last_score,
        question_type=state.current_question_type or QuestionType.THEORY,
        consecutive_follow_ups=state.consecutive_follow_ups,
        answer=last_answer_text,
    )

    if do_followup:
        logger.info(f"[{state.session_id}] Socratic mode activated: {followup_reason}")
        followup_q = await generate_socratic_followup(
            topic=state.current_topic or "",
            original_question=state.current_question or "",
            candidate_answer=last_answer_text,
            score=last_score,
            difficulty=state.current_difficulty,
        )
        state.current_question = followup_q
        state.current_question_type = QuestionType.FOLLOW_UP
        state.consecutive_follow_ups += 1
        state.is_followup_question = True
        state.questions_asked += 1
        state.current_reasoning_trace = ReasoningTrace(
            proposing_agent="socratic_engine",
            chief_rationale=followup_reason,
            human_explanation=f"I noticed your answer on {state.current_topic} had some gaps. Let me probe a bit deeper.",
            difficulty_rationale="Same difficulty — drilling into your specific answer.",
        )
        return state

    # Reset follow-up counter when we move to a new topic
    state.consecutive_follow_ups = 0
    state.is_followup_question = False
    # ────────────────────────────────────────────────────────────────────

    # Check Completion conditions
    if (state.questions_asked >= settings.MIN_QUESTIONS and 
        len(state.curriculum_days_covered) >= settings.MIN_CURRICULUM_DAYS) or \
       state.questions_asked >= settings.MAX_QUESTIONS:
        state.status = InterviewStatus.COMPLETE
        return state
        
    graph: KnowledgeGraph = _sessions[state.session_id]["graph"]
    memory: MemoryEngine = _sessions[state.session_id]["memory"]
    
    weak_topics = [
        t for t, c in graph.get_all_scores().items()
        if c < 0.65 and t not in state.topics_covered[-2:]
    ]
    
    plan = await plan_next_question(
        topic=state.current_topic or "",
        weak_topics=weak_topics,
        topics_covered=state.topics_covered,
        days_covered=state.curriculum_days_covered,
        confidence_score=0.5,
        consecutive_correct=state.consecutive_correct,
        consecutive_wrong=state.consecutive_wrong,
        recent_context=await memory.get_context_for_llm(current_topic=state.current_topic),
        questions_asked=state.questions_asked,
        min_questions=settings.MIN_QUESTIONS,
        min_days=settings.MIN_CURRICULUM_DAYS,
    )
    
    next_topic = plan.get("next_topic", state.current_topic)
    next_type = QuestionType(plan.get("question_type", "theory"))
    next_diff = DifficultyLevel(min(max(int(plan.get("difficulty", 2)), 1), 7))
    
    # If the LLM planning failed (controlled fallback), use the knowledge graph
    # to deterministically select a topic from an uncovered curriculum day.
    # This ensures the interview progresses toward the 4-day requirement even
    # when the local model cannot produce a valid plan.
    used_fallback = bool(plan.get("fallback"))
    if used_fallback:
        uncovered_days = sorted(
            {d for d in range(1, 26) if d not in state.curriculum_days_covered}
        )
        fallback_topic = None
        for day in uncovered_days:
            candidates = [
                t for t in graph.get_topics_for_day(day)
                if t not in state.topics_covered
            ]
            if candidates:
                fallback_topic = candidates[0]
                break
        if fallback_topic:
            next_topic = fallback_topic
            next_type = QuestionType.THEORY
            next_diff = DifficultyLevel.MEDIUM
    
    state.questions_asked += 1
    state.current_topic = next_topic
    state.current_question_type = next_type
    state.current_difficulty = next_diff
    state.current_curriculum_day = graph.get_curriculum_day(next_topic)
    
    # Build Explainable AI reasoning trace from the actual planning decision.
    # Uses only the decision metadata produced by the planning agent — no hidden chain-of-thought.
    state.current_reasoning_trace = ReasoningTrace(
        weak_node=next_topic if next_topic in weak_topics else None,
        dependency_path=graph.get_dependency_path(next_topic),
        proposing_agent="chief_interview_agent",
        chief_rationale=plan.get("rationale", "Next topic selected based on interview progress."),
        human_explanation=plan.get(
            "human_explanation",
            f"Moving on to {next_topic} to continue assessing your knowledge.",
        ),
        difficulty_rationale=(
            f"Difficulty set to level {next_diff.value} based on your recent performance."
        ),
    )
    
    return state


# ─────────────────────────────────────────────
# Edge Routing
# ─────────────────────────────────────────────

def route_after_planning(state: InterviewState) -> str:
    """Route to generation or end."""
    if state.status == InterviewStatus.COMPLETE:
        return END
    return "generate_question"

# ─────────────────────────────────────────────
# Graph Construction
# ─────────────────────────────────────────────

workflow = StateGraph(InterviewState)
workflow.add_node("profile_analysis", node_profile_analysis)
workflow.add_node("generate_question", node_generate_question)

# Initialization Flow
workflow.set_entry_point("profile_analysis")
workflow.add_edge("profile_analysis", "generate_question")
workflow.add_edge("generate_question", END)

# NOTE: evaluate_answer, memory_update, and plan_next are intentionally NOT
# declared on the main init graph — they are only used in the dynamic response
# sub-graph built inside respond_to_question(). Declaring them here made them
# unreachable, which caused langgraph.compile() to fail validation.

# Response Flow
# To hook into LangGraph manually without cyclical hanging:
# We execute sub-graphs when API endpoints are hit.
app = workflow.compile()


# ─────────────────────────────────────────────
# Public API Methods
# ─────────────────────────────────────────────

def restore_session_engines(state: InterviewState):
    """Reconstruct KnowledgeGraph and MemoryEngine from InterviewState to support service logic."""
    graph = KnowledgeGraph()
    for topic, confidence in state.candidate.learning_signals.items():
        graph.update_confidence(topic, confidence)
    for topic, confidence in state.topic_confidence.items():
        graph.update_confidence(topic, confidence)
        
    memory = MemoryEngine(session_id=state.session_id)
    # Re-hydrate short term memory only for active state tracking
    for qa in state.qa_history:
        memory.short_term.add(
            question=qa.get("question", ""),
            answer=qa.get("answer", ""),
            topic=qa.get("topic", "Unknown"),
            score=qa.get("score", 0.5),
        )
    _sessions[state.session_id] = {
        "state": state,
        "graph": graph,
        "memory": memory,
    }


async def get_or_load_session(session_id: str) -> InterviewState:
    """Retrieve session from in-memory cache, or load from DB if cache miss."""
    if session_id in _sessions:
        return _sessions[session_id]["state"]
        
    try:
        from db.database import AsyncSessionLocal, InterviewSession
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            stmt = select(InterviewSession).where(InterviewSession.session_id == session_id)
            result = await session.execute(stmt)
            db_sess = result.scalar_one_or_none()
            if db_sess and db_sess.state_json:
                state = InterviewState.model_validate(db_sess.state_json)
                restore_session_engines(state)
                return state
    except Exception as e:
        logger.warning(f"Database unavailable or failed to load session: {e}")
        
    raise ValueError(f"Session {session_id} not found")


async def start_interview(request: StartInterviewRequest) -> StartInterviewResponse:
    """Initialize session and run Graph to generate first question."""
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    logger.info(f"[{session_id}] Initializing new interview session.")
    
    candidate = CandidateProfile(
        candidate_id=request.candidate_id or f"cand_{uuid.uuid4().hex[:8]}",
        name=request.name,
        completed_missions=request.completed_missions,
        skipped_topics=request.skipped_topics,
        learning_signals=request.learning_signals or {},
    )
    
    state = InterviewState(
        session_id=session_id,
        candidate=candidate,
        status=InterviewStatus.IN_PROGRESS,
    )
    
    # Pre-populate in-memory storage so nodes can register memory/graph engines
    _sessions[session_id] = {"state": state}
    
    try:
        # Run graph execution (INIT -> PROFILE_ANALYSIS -> QUESTION)
        final_state = InterviewState(**await app.ainvoke(state))
        _sessions[session_id]["state"] = final_state
        
        # Persist session to database (within a transactional block)
        try:
            from db.database import AsyncSessionLocal, InterviewSession, QuestionRecord
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Create interview session entry
                    db_session = InterviewSession(
                        session_id=session_id,
                        candidate_id=candidate.candidate_id,
                        candidate_name=candidate.name,
                        status="in_progress",
                        state_json=final_state.model_dump(),
                        total_questions=1,
                    )
                    session.add(db_session)
                    
                    # Create first question record
                    db_question = QuestionRecord(
                        session_id=session_id,
                        question_number=1,
                        question_text=final_state.current_question or "",
                        question_type=final_state.current_question_type.value if final_state.current_question_type else "theory",
                        topic=final_state.current_topic or "",
                        curriculum_day=final_state.current_curriculum_day,
                        difficulty_level=final_state.current_difficulty.value if final_state.current_difficulty else 1,
                    )
                    session.add(db_question)
            logger.info(f"[{session_id}] Session persisted to database successfully.")
        except Exception as db_err:
            logger.warning(f"Database persistence skipped/failed: {db_err}")
            
        return StartInterviewResponse(
            session_id=session_id,
            candidate_id=candidate.candidate_id,
            status=InterviewStatus.IN_PROGRESS,
            question_number=1,
            question=final_state.current_question or "",
            question_type=final_state.current_question_type or QuestionType.THEORY,
            topic=final_state.current_topic or "",
            curriculum_day=final_state.current_curriculum_day,
            difficulty_level=final_state.current_difficulty,
            reasoning_trace=final_state.current_reasoning_trace or ReasoningTrace(human_explanation="Session initialized."),
            total_questions_planned=settings.MIN_QUESTIONS,
        )
        
    except Exception as e:
        logger.error(f"[{session_id}] Failed to start interview session: {e}")
        if session_id in _sessions:
            del _sessions[session_id]
        raise RuntimeError(f"Could not initialize interview session: {str(e)}")


async def respond_to_question(request: RespondRequest) -> RespondResponse:
    """Process candidate answer through the LangGraph execution loop."""
    state = await get_or_load_session(request.session_id)
    
    # Store information about the question currently being answered
    answered_q_num = state.questions_asked
    answered_q_text = state.current_question or ""
    answered_q_type = state.current_question_type
    answered_topic = state.current_topic or ""
    answered_day = state.current_curriculum_day
    answered_diff = state.current_difficulty
    
    state.last_answer = request.answer
    
    # We dynamically build the response execution graph so we can ainvoke it
    resp_workflow = StateGraph(InterviewState)
    resp_workflow.add_node("evaluate", node_evaluate_answer)
    resp_workflow.add_node("memory", node_memory_update)
    resp_workflow.add_node("plan", node_plan_next)
    resp_workflow.add_node("generate", node_generate_question)
    
    resp_workflow.set_entry_point("evaluate")
    resp_workflow.add_edge("evaluate", "memory")
    resp_workflow.add_edge("memory", "plan")
    
    def conditional_end(s: InterviewState):
        return END if s.status == InterviewStatus.COMPLETE else "generate"
        
    resp_workflow.add_conditional_edges("plan", conditional_end)
    resp_workflow.add_edge("generate", END)
    
    resp_app = resp_workflow.compile()
    
    # Execute the response chain
    final_state = InterviewState(**await resp_app.ainvoke(state))
    _sessions[request.session_id]["state"] = final_state
    
    # Sync update to database
    try:
        from db.database import AsyncSessionLocal, InterviewSession, QuestionRecord
        from sqlalchemy import select, update
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # 1. Update the answered question record with response details
                stmt = select(QuestionRecord).where(
                    QuestionRecord.session_id == request.session_id,
                    QuestionRecord.question_number == answered_q_num
                )
                res = await session.execute(stmt)
                db_question = res.scalar_one_or_none()
                if db_question:
                    db_question.answer_text = request.answer
                    db_question.answer_score = final_state.last_answer_score
                else:
                    # Fallback create if missing
                    db_question = QuestionRecord(
                        session_id=request.session_id,
                        question_number=answered_q_num,
                        question_text=answered_q_text,
                        question_type=answered_q_type.value if answered_q_type else "theory",
                        topic=answered_topic,
                        curriculum_day=answered_day,
                        difficulty_level=answered_diff.value if answered_diff else 1,
                        answer_text=request.answer,
                        answer_score=final_state.last_answer_score,
                    )
                    session.add(db_question)
                
                # 2. If new question is generated and interview is not complete, insert it
                if final_state.status != InterviewStatus.COMPLETE:
                    db_next_question = QuestionRecord(
                        session_id=request.session_id,
                        question_number=final_state.questions_asked,
                        question_text=final_state.current_question or "",
                        question_type=final_state.current_question_type.value if final_state.current_question_type else "theory",
                        topic=final_state.current_topic or "",
                        curriculum_day=final_state.current_curriculum_day,
                        difficulty_level=final_state.current_difficulty.value if final_state.current_difficulty else 1,
                    )
                    session.add(db_next_question)
                
                # 3. Update interview session
                stmt_sess = select(InterviewSession).where(InterviewSession.session_id == request.session_id)
                res_sess = await session.execute(stmt_sess)
                db_sess = res_sess.scalar_one_or_none()
                if db_sess:
                    db_sess.status = final_state.status.value
                    db_sess.state_json = final_state.model_dump()
                    db_sess.total_questions = final_state.questions_asked
                    if final_state.status == InterviewStatus.COMPLETE:
                        import datetime
                        db_sess.completed_at = datetime.datetime.utcnow()
    except Exception as db_err:
        logger.warning(f"Database response sync skipped/failed: {db_err}")
        
    return RespondResponse(
        session_id=request.session_id,
        question_number=final_state.questions_asked,
        question=final_state.current_question,
        question_type=final_state.current_question_type,
        topic=final_state.current_topic,
        curriculum_day=final_state.current_curriculum_day,
        difficulty_level=final_state.current_difficulty,
        reasoning_trace=final_state.current_reasoning_trace,
        answer_score=final_state.last_answer_score,
        answer_feedback=final_state.last_answer_feedback,
        strong_points=final_state.last_strong_points,
        key_gaps=final_state.last_key_gaps,
        is_followup=final_state.is_followup_question,
        interview_complete=(final_state.status == InterviewStatus.COMPLETE),
        questions_remaining=max(0, settings.MIN_QUESTIONS - final_state.questions_asked),
        message=(
            "Interview complete"
            if final_state.status == InterviewStatus.COMPLETE
            else ("Follow-up question" if final_state.is_followup_question else "Next question")
        ),
    )


async def get_report(session_id: str) -> FeedbackReport:
    """Generate final report and persist to database."""
    state = await get_or_load_session(session_id)
    report = await generate_report(state)
    
    # Save report to DB
    try:
        from db.database import AsyncSessionLocal, InterviewSession
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            async with session.begin():
                stmt = select(InterviewSession).where(InterviewSession.session_id == session_id)
                res = await session.execute(stmt)
                db_sess = res.scalar_one_or_none()
                if db_sess:
                    db_sess.report_json = report.model_dump()
                    db_sess.overall_score = report.overall_score
    except Exception as db_err:
        logger.warning(f"Database report sync skipped/failed: {db_err}")
        
    return report

