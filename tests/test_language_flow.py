import pytest
from backend.agents.interview_agents import generate_question
from backend.models.interview import QuestionType, DifficultyLevel

@pytest.mark.asyncio
async def test_language_flow_telugu():
    """
    Verify that when language='te' is requested, the LLM generates a question in Telugu.
    This fulfills the critical product requirement for end-to-end language integration.
    """
    topic = "Python Basics"
    question_type = QuestionType.THEORY
    difficulty = DifficultyLevel.EASY
    language = "te"

    question = await generate_question(
        topic=topic,
        question_type=question_type,
        difficulty=difficulty,
        language=language
    )

    # Simple heuristic to verify it's not English.
    # We can check if typical English words are absent, or just ensure it's returned.
    # In a real CI environment, we might use a language detection library like langdetect.
    # For now, we assert it returns a non-empty string and we print it.
    assert question is not None
    assert len(question) > 5

    # Check for common English structural words which shouldn't dominate a Telugu sentence
    english_stop_words = [" the ", " is ", " and ", " what "]
    english_word_count = sum(1 for word in english_stop_words if word in question.lower())
    
    # We allow maybe 1 or 2 if it's a technical term (like "Python"), but not common stop words.
    assert english_word_count < 2, f"Question appears to be in English instead of Telugu: {question}"

@pytest.mark.asyncio
async def test_language_flow_spanish():
    """
    Verify that when language='es' is requested, the LLM generates a question in Spanish.
    """
    question = await generate_question(
        topic="Data Structures",
        question_type=QuestionType.CODING,
        difficulty=DifficultyLevel.MEDIUM,
        language="es"
    )

    assert question is not None
    assert len(question) > 5
    
    # "que", "como", "escribe" are common in Spanish coding questions
    assert any(word in question.lower() for word in ["que", "escribe", "como", "dato", "array", "dado", "estructura"]), f"Question does not look Spanish: {question}"
