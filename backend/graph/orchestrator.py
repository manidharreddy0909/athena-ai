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
    _sessions[state.session_id]["memory"] = MemoryEngine()
    
    return state


async def node_generate_question(state: InterviewState) -> InterviewState:
    """Generate the actual question text using LLM."""
    logger.info(f"[{state.session_id}] Executing QUESTION generation")
    
    memory = _sessions[state.session_id]["memory"]
    
    # Ensure a valid question type is set on state (defaults to theory for the first question)
    if state.current_question_type is None:
        state.current_question_type = QuestionType.THEORY
    
    question = await generate_question(
        topic=state.current_topic or "AI Foundations",
        question_type=state.current_question_type,
        difficulty=state.current_difficulty,
        context=memory.get_context_for_llm(),
        last_answer=state.last_answer,
        candidate_name=state.candidate.name,
    )
    
    state.current_question = question
    
    if state.questions_asked == 0:
        state.questions_asked = 1 # Initial start
        
    return state


async def node_evaluate_answer(state: InterviewState) -> InterviewState:
    """Evaluate candidate answer."""
    logger.info(f"[{state.session_id}] Executing EVALUATION")
    
    if not state.last_answer:
        return state
        
    evaluation = await evaluate_answer(
        question=state.current_question or "",
        answer=state.last_answer,
        topic=state.current_topic or "",
        question_type=state.current_question_type or QuestionType.THEORY,
        difficulty=state.current_difficulty,
    )
    
    state.last_answer_score = evaluation.get("score", 0.5)
    state.last_answer_feedback = evaluation.get("feedback", "")
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
    memory.record_qa(
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
        recent_context=memory.get_context_for_llm(),
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

async def start_interview(request: StartInterviewRequest) -> StartInterviewResponse:
    """Initialize session and run Graph to generate first question."""
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    
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
    
    _sessions[session_id] = {"state": state}
    
    # Run the init subgraph (Profile Analysis -> Generate Question)
    # LangGraph returns a dict-like AddableValuesDict; reconstruct the Pydantic state.
    final_state = InterviewState(**await app.ainvoke(state))
    _sessions[session_id]["state"] = final_state
    
    return StartInterviewResponse(
        session_id=session_id,
        candidate_id=candidate.candidate_id,
        status=InterviewStatus.IN_PROGRESS,
        question_number=1,
        question=final_state.current_question,
        question_type=final_state.current_question_type,
        topic=final_state.current_topic,
        curriculum_day=final_state.current_curriculum_day,
        difficulty_level=final_state.current_difficulty,
        reasoning_trace=final_state.current_reasoning_trace,
        total_questions_planned=settings.MIN_QUESTIONS,
    )


async def respond_to_question(request: RespondRequest) -> RespondResponse:
    """Process candidate answer through the LangGraph execution loop."""
    if request.session_id not in _sessions:
        raise ValueError("Session not found")
        
    state = _sessions[request.session_id]["state"]
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
    # LangGraph returns a dict-like AddableValuesDict; reconstruct the Pydantic state.
    final_state = InterviewState(**await resp_app.ainvoke(state))
    _sessions[request.session_id]["state"] = final_state
    
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
        interview_complete=(final_state.status == InterviewStatus.COMPLETE),
        questions_remaining=max(0, settings.MIN_QUESTIONS - final_state.questions_asked),
        message="Interview complete" if final_state.status == InterviewStatus.COMPLETE else "Next question",
    )


async def get_report(session_id: str) -> FeedbackReport:
    """Generate final report."""
    if session_id not in _sessions:
        raise ValueError("Session not found")
        
    state = _sessions[session_id]["state"]
    return await generate_report(state)
