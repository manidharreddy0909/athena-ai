"""
Athena AI — Question Generator Agent
Generates questions based on topic, type, difficulty, and candidate context
"""
from core.llm import chat_completion, chat_completion_with_retry, parse_json_response
from models.interview import QuestionType, DifficultyLevel, ReasoningTrace
from loguru import logger


QUESTION_PROMPTS = {
    QuestionType.THEORY: "Ask a clear conceptual question about {topic}. The candidate should explain what it is, how it works, and why it matters.",
    QuestionType.CODING: "Ask the candidate to write code related to {topic}. Make it practical and achievable in 5-10 minutes.",
    QuestionType.DEBUGGING: "Present a broken code snippet or failing system related to {topic} and ask the candidate to diagnose and fix it.",
    QuestionType.ARCHITECTURE: "Ask the candidate to design a system or component that uses {topic}. Focus on design decisions and tradeoffs.",
    QuestionType.SYSTEM_DESIGN: "Ask the candidate to design a production-scale system using {topic} at significant scale (1M+ requests or documents).",
    QuestionType.OPTIMIZATION: "Ask the candidate how they would improve the latency, cost, or accuracy of a system using {topic}.",
    QuestionType.EDGE_CASE: "Ask about a failure mode, edge case, or limitation of {topic} in production.",
    QuestionType.FOLLOW_UP: "Based on the candidate's last answer about {topic}, ask a probing follow-up that goes deeper.",
}

DIFFICULTY_MODIFIERS = {
    DifficultyLevel.EASY: "Keep this beginner-friendly. Use simple language.",
    DifficultyLevel.MEDIUM: "This is a mid-level question. Expect a clear explanation with an example.",
    DifficultyLevel.HARD: "This is a hard question. Expect the candidate to demonstrate practical experience.",
    DifficultyLevel.EXPERT: "This is an expert-level question. Expect precise technical detail and tradeoff analysis.",
    DifficultyLevel.RESEARCH: "This is a research-level question. Ask about limitations, recent advances, or open problems.",
    DifficultyLevel.SYSTEM_DESIGN: "This is a system design question. The candidate should consider scale, reliability, and cost.",
    DifficultyLevel.PRODUCTION_SCALE: "This is a production-scale challenge. The candidate should think like a senior engineer debugging a live system.",
}

# Minimal schema - matches what Gemma 4 / LM Studio can reliably produce
EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "feedback": {"type": "string"},
    },
    "required": ["score", "feedback"],
}

PLANNING_SCHEMA = {
    "type": "object",
    "properties": {
        "next_topic": {"type": "string"},
        "question_type": {"type": "string"},
        "difficulty": {"type": "integer"},
        "rationale": {"type": "string"},
    },
    "required": ["next_topic", "question_type", "difficulty", "rationale"],
}


async def generate_question(
    topic: str,
    question_type: QuestionType,
    difficulty: DifficultyLevel,
    context: str = "",
    last_answer: str = "",
    candidate_name: str = "the candidate",
) -> str:
    """Generate a single interview question using the LLM."""

    type_prompt = QUESTION_PROMPTS.get(question_type, QUESTION_PROMPTS[QuestionType.THEORY])
    type_prompt = type_prompt.format(topic=topic)
    difficulty_mod = DIFFICULTY_MODIFIERS.get(difficulty, "")

    messages = [
        {
            "role": "system",
            "content": (
                "You are Athena, a senior AI/ML interview specialist. "
                "Generate ONE clear, specific interview question. "
                "Do NOT include the answer. Do NOT explain the question. "
                "Output ONLY the question text. "
                "Make it conversational and professional."
            ),
        },
        {
            "role": "user",
            "content": f"""Topic: {topic}
Question Type: {question_type.value}
Difficulty: Level {difficulty.value} — {difficulty_mod}
Instruction: {type_prompt}

{f"Recent context: {context}" if context else ""}
{f"Candidate's last answer to consider for follow-up: {last_answer[:500]}" if last_answer and question_type == QuestionType.FOLLOW_UP else ""}

Generate exactly one interview question:""",
        },
    ]

    try:
        question = await chat_completion(messages, temperature=0.8, max_tokens=256)
        question = question.strip().strip('"').strip("'")
        logger.debug(f"📝 Generated {question_type.value} question on {topic}: {question[:80]}...")
        return question
    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        # Fallback question
        return f"Can you explain what {topic} is and how it works in a real AI system?"


async def evaluate_answer(
    question: str,
    answer: str,
    topic: str,
    question_type: QuestionType,
    difficulty: DifficultyLevel,
) -> dict:
    """
    Evaluate a candidate's answer.
    Returns: score (0-1), feedback, dimension_scores
    """
    # Truncate excessively large candidate answers to keep the prompt focused
    # for the local model.
    truncated_answer = answer[:500] if answer else ""

    messages = [
        {
            "role": "user",
            "content": f"""You are an expert AI interview evaluator.

Question: {question[:200]}
Topic: {topic}
Type: {question_type.value}
Difficulty: {difficulty.value}/7
Candidate's Answer: {truncated_answer}

Evaluate the answer. Respond with valid JSON only, no explanation:
{{"score": <float 0.0-1.0>, "feedback": "<2 sentence assessment>"}}""",
        },
    ]

    try:
        result_str = await chat_completion_with_retry(
            messages, temperature=0.3, max_tokens=300, json_mode=False, use_breath_layer=True
        )
        result = parse_json_response(result_str)
        return {
            "score": float(result.get("score", 0.5)),
            "technical_accuracy": float(result.get("technical_accuracy", result.get("score", 0.5))),
            "depth": float(result.get("depth", result.get("score", 0.5))),
            "clarity": float(result.get("clarity", result.get("score", 0.5))),
            "feedback": str(result.get("feedback", "Answer recorded.")),
            "key_gaps": result.get("key_gaps", []),
            "strong_points": result.get("strong_points", []),
        }
    except Exception as e:
        logger.error(f"Evaluation failed after retries: {e}")
        # Controlled fallback — clearly not an LLM decision.
        return {
            "score": 0.5,
            "technical_accuracy": 0.5,
            "depth": 0.5,
            "clarity": 0.5,
            "feedback": "Answer recorded. Moving to the next question.",
            "key_gaps": [],
            "strong_points": [],
        }


async def plan_next_question(
    topic: str,
    weak_topics: list[str],
    topics_covered: list[str],
    days_covered: list[int],
    confidence_score: float,
    consecutive_correct: int,
    consecutive_wrong: int,
    recent_context: str,
    questions_asked: int,
    min_questions: int = 8,
    min_days: int = 4,
) -> dict:
    """
    Chief Interview Agent: decides next topic, type, and difficulty.
    Returns: {topic, question_type, difficulty, rationale}
    """
    days_needed = max(0, min_days - len(days_covered))

    messages = [
        {
            "role": "user",
            "content": f"""You are the Chief Interview Agent. Decide the next interview question.

State: asked={questions_asked}/{min_questions}, days={days_covered}, need_days={days_needed}, weak={weak_topics[:3]}, topic={topic}, correct_streak={consecutive_correct}, wrong_streak={consecutive_wrong}, recent={topics_covered[-3:] if topics_covered else []}.

Rules: prioritize uncovered days if days_needed>0; lower difficulty if wrong_streak>=2; raise difficulty if correct_streak>=3; avoid recent topics.

Respond with valid JSON only:
{{"next_topic": "<topic>", "question_type": "<theory|coding|debugging|architecture>", "difficulty": <1-7>, "rationale": "<reason>"}}""",
        },
    ]

    try:
        result_str = await chat_completion_with_retry(
            messages, temperature=0.4, max_tokens=200, json_mode=False, use_breath_layer=True
        )
        result = parse_json_response(result_str)
        return {
            "next_topic": str(result.get("next_topic", topic)),
            "question_type": str(result.get("question_type", "theory")),
            "difficulty": int(result.get("difficulty", 2)),
            "rationale": str(result.get("rationale", "")),
            "human_explanation": str(result.get("human_explanation", "")),
        }
    except Exception as e:
        logger.error(f"Planning failed after retries: {e}")
        # Controlled fallback — clearly not an LLM decision.
        # Pick a topic from an uncovered curriculum day to ensure progress.
        fallback_topic = weak_topics[0] if weak_topics else topic
        return {
            "next_topic": fallback_topic,
            "question_type": "theory",
            "difficulty": 2,
            "rationale": "Fallback decision (LLM unavailable)",
            "human_explanation": f"Exploring your knowledge of {fallback_topic}.",
            "fallback": True,
        }
