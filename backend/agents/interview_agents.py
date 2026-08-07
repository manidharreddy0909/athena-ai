"""
Athena AI — Question Generator Agent
Generates questions based on topic, type, difficulty, and candidate context
"""
import json
from core.llm import chat_completion
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
    messages = [
        {
            "role": "system",
            "content": (
                "You are Athena, an expert AI interview evaluator. "
                "Evaluate the candidate's answer and return a JSON object. "
                "Be fair but rigorous. Consider technical accuracy, depth, and clarity."
            ),
        },
        {
            "role": "user",
            "content": f"""Question: {question}
Topic: {topic}
Type: {question_type.value}
Difficulty Level: {difficulty.value}/7

Candidate's Answer: {answer}

Evaluate and return JSON with this exact structure:
{{
  "score": <float 0.0-1.0>,
  "technical_accuracy": <float 0.0-1.0>,
  "depth": <float 0.0-1.0>,
  "clarity": <float 0.0-1.0>,
  "feedback": "<2-3 sentence constructive feedback>",
  "key_gaps": ["<gap1>", "<gap2>"],
  "strong_points": ["<point1>"]
}}""",
        },
    ]

    try:
        result_str = await chat_completion(messages, temperature=0.3, max_tokens=512, json_mode=True)
        result = json.loads(result_str)
        return result
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
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
            "role": "system",
            "content": (
                "You are the Chief Interview Agent for Athena AI. "
                "You must decide what to ask next based on the candidate's performance. "
                "Return a JSON object with your decision."
            ),
        },
        {
            "role": "user",
            "content": f"""Interview state:
- Questions asked: {questions_asked}
- Minimum required: {min_questions}
- Topics covered: {topics_covered}
- Curriculum days covered: {days_covered}
- Days still needed: {days_needed}
- Weak topics: {weak_topics[:5]}
- Current topic: {topic}
- Confidence score: {confidence_score:.2f}
- Consecutive correct: {consecutive_correct}
- Consecutive wrong: {consecutive_wrong}
- Recent context: {recent_context[:300]}

Rules:
1. If days_needed > 0, prioritize topics from uncovered days
2. If confidence < 0.4, drop difficulty and revisit fundamentals
3. If consecutive_correct >= 3, increase difficulty
4. If consecutive_wrong >= 2, decrease difficulty or change topic
5. Never repeat recently covered topics unless doing follow-up

Return JSON:
{{
  "next_topic": "<topic from the curriculum>",
  "question_type": "<theory|coding|debugging|architecture|system_design|optimization|edge_case|follow_up>",
  "difficulty": <1-7>,
  "rationale": "<why this decision>",
  "human_explanation": "<short explanation for the candidate-facing UI>"
}}""",
        },
    ]

    try:
        result_str = await chat_completion(messages, temperature=0.4, max_tokens=512, json_mode=True)
        result = json.loads(result_str)
        return result
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        # Fallback: pick first weak topic
        fallback_topic = weak_topics[0] if weak_topics else topic
        return {
            "next_topic": fallback_topic,
            "question_type": "theory",
            "difficulty": 2,
            "rationale": "Fallback decision",
            "human_explanation": f"Exploring your knowledge of {fallback_topic}.",
        }
