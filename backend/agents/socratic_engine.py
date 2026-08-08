"""
Athena AI — Socratic Intelligence Engine (Phase 5)
Implements adaptive follow-up logic based on answer analysis.
Decides WHEN to drill deeper vs. when to move to a new topic.
"""
from typing import Optional
from loguru import logger

from core.llm import chat_completion_with_retry, parse_json_response, LogicRole
from models.interview import QuestionType, DifficultyLevel


# Score thresholds for Socratic mode
SOCRATIC_THRESHOLD = 0.75     # Above this = candidate knows it, move on
PROBE_THRESHOLD = 0.45        # Below this = candidate is lost, scaffold up
MAX_FOLLOW_UPS_PER_TOPIC = 2  # Prevent infinite drilling on one topic


async def should_follow_up(
    score: float,
    question_type: QuestionType,
    consecutive_follow_ups: int,
    answer: str,
) -> tuple[bool, str]:
    """
    Decide if Athena should ask a Socratic follow-up on the SAME topic.

    Returns: (should_follow_up: bool, reason: str)
    """
    # Guard: never chain more than MAX_FOLLOW_UPS_PER_TOPIC deep
    if consecutive_follow_ups >= MAX_FOLLOW_UPS_PER_TOPIC:
        return False, "Max follow-up depth reached — rotating to new topic."

    # If the candidate aced it, no need to probe further
    if score >= SOCRATIC_THRESHOLD:
        return False, f"Score {score:.2f} indicates strong understanding — advancing."

    # Very weak answer: don't drill, instead scaffold (lower difficulty) on new topic
    if score < PROBE_THRESHOLD and question_type != QuestionType.FOLLOW_UP:
        return False, f"Score {score:.2f} too low — candidate needs scaffolding, not drilling."

    # The sweet spot: candidate partially answered (0.45–0.74), follow up to probe deeper
    if PROBE_THRESHOLD <= score < SOCRATIC_THRESHOLD and len(answer) > 30:
        return True, f"Score {score:.2f} suggests partial understanding — probing deeper."

    return False, "Default: advancing to next topic."


async def generate_socratic_followup(
    topic: str,
    original_question: str,
    candidate_answer: str,
    score: float,
    difficulty: DifficultyLevel,
) -> str:
    """
    Generate a targeted Socratic follow-up question based on the candidate's specific answer.
    This is NOT a generic follow-up — it explicitly references what the candidate said.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are Athena, a Socratic AI interviewer. Your job is to probe deeper "
                "into a candidate's answer to expose gaps or test real understanding. "
                "Do NOT repeat the original question. DO reference specific things the "
                "candidate said. Ask exactly ONE probing follow-up question. "
                "Output ONLY the question text — no preamble, no explanation."
            ),
        },
        {
            "role": "user",
            "content": f"""Topic: {topic}
Original Question: {original_question}
Candidate's Answer: {candidate_answer[:600]}
Score: {score:.2f}/1.0 (partial — they know some but not all)

Based on what they said, generate one precise follow-up question that:
1. Probes a specific gap or vague statement in their answer
2. Tests whether they truly understand the mechanism, not just the buzzword
3. Could not be answered with a simple yes/no

Follow-up question:""",
        },
    ]

    try:
        followup = await chat_completion_with_retry(
            messages,
            temperature=0.85,
            max_tokens=200,
            role=LogicRole.INTERVIEWER,
        )
        followup = followup.strip().strip('"').strip("'")
        logger.info(f"🔍 Socratic follow-up generated for {topic}: {followup[:80]}...")
        return followup
    except Exception as e:
        logger.warning(f"Socratic follow-up generation failed: {e}")
        return f"Can you elaborate more specifically on how {topic} works under the hood?"


async def deep_evaluate_answer(
    question: str,
    answer: str,
    topic: str,
    question_type: QuestionType,
    difficulty: DifficultyLevel,
) -> dict:
    """
    Extended evaluation: returns score + structured feedback + dimensions + gaps.
    Used for Phase 5 rich feedback panel.
    """
    truncated = answer[:700] if answer else "(no answer)"

    messages = [
        {
            "role": "user",
            "content": f"""You are an expert AI/ML interview evaluator. Evaluate this answer rigorously.

Topic: {topic}
Question Type: {question_type.value}
Difficulty: {difficulty.value}/7
Question: {question[:300]}
Candidate Answer: {truncated}

Return valid JSON with this exact structure:
{{
  "score": <float 0.0-1.0>,
  "technical_accuracy": <float 0.0-1.0>,
  "depth": <float 0.0-1.0>,
  "clarity": <float 0.0-1.0>,
  "practical_experience": <float 0.0-1.0>,
  "feedback": "<2-3 sentence balanced assessment>",
  "strong_points": ["<specific strength 1>", "<specific strength 2>"],
  "key_gaps": ["<specific gap 1>", "<specific gap 2>"],
  "follow_up_suggestion": "<one thing worth probing deeper if needed>"
}}""",
        },
    ]

    try:
        result_str = await chat_completion_with_retry(
            messages,
            temperature=0.2,
            max_tokens=500,
            role=LogicRole.EVALUATOR,
        )
        result = parse_json_response(result_str)
        base_score = float(result.get("score", 0.5))
        return {
            "score": base_score,
            "technical_accuracy": float(result.get("technical_accuracy", base_score)),
            "depth": float(result.get("depth", base_score)),
            "clarity": float(result.get("clarity", base_score)),
            "practical_experience": float(result.get("practical_experience", base_score)),
            "feedback": str(result.get("feedback", "Answer recorded.")),
            "strong_points": result.get("strong_points", []),
            "key_gaps": result.get("key_gaps", []),
            "follow_up_suggestion": str(result.get("follow_up_suggestion", "")),
        }
    except Exception as e:
        logger.error(f"Deep evaluation failed: {e}")
        return {
            "score": 0.5,
            "technical_accuracy": 0.5,
            "depth": 0.5,
            "clarity": 0.5,
            "practical_experience": 0.5,
            "feedback": "Answer recorded. Moving to the next question.",
            "strong_points": [],
            "key_gaps": [],
            "follow_up_suggestion": "",
        }
