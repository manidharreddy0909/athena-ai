"""
Athena AI — Four-Layer Memory System
Layer 1: Short-Term  (in-memory list)
Layer 2: Semantic    (Qdrant vector search)
Layer 3: Interview   (PostgreSQL structured state)
Layer 4: Reasoning   (JSON blobs — agent debate logs)
"""
from typing import Optional
from loguru import logger


class ShortTermMemory:
    """
    Layer 1: Last N Q&A pairs in the current session.
    Prepended directly into LLM prompts as conversation history.
    """

    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self._store: list[dict] = []

    def add(self, question: str, answer: str, topic: str, score: Optional[float] = None):
        entry = {
            "question": question,
            "answer": answer,
            "topic": topic,
            "score": score,
        }
        self._store.append(entry)
        if len(self._store) > self.max_size:
            self._store.pop(0)

    def get_recent(self, n: int = 3) -> list[dict]:
        return self._store[-n:]

    def to_prompt_context(self) -> str:
        """Format recent Q&A as LLM context string."""
        if not self._store:
            return "No previous questions yet."
        lines = []
        for i, entry in enumerate(self._store, 1):
            lines.append(f"Q{i} [{entry['topic']}]: {entry['question']}")
            lines.append(f"A{i}: {entry['answer'][:300]}...")
        return "\n".join(lines)

    def get_recent_topics(self) -> list[str]:
        return [e["topic"] for e in self._store[-3:]]


class ReasoningMemory:
    """
    Layer 4: Full agent debate logs per question.
    Used for Explainable AI panel and recruiter report.
    """

    def __init__(self):
        self._store: list[dict] = []

    def add_debate_round(
        self,
        question_number: int,
        topic: str,
        agent_opinions: dict[str, str],
        chief_decision: str,
        selected_question: str,
        reasoning_trace: dict,
    ):
        self._store.append({
            "question_number": question_number,
            "topic": topic,
            "agent_opinions": agent_opinions,
            "chief_decision": chief_decision,
            "selected_question": selected_question,
            "reasoning_trace": reasoning_trace,
        })

    def get_all(self) -> list[dict]:
        return self._store

    def get_for_question(self, question_number: int) -> Optional[dict]:
        for entry in self._store:
            if entry["question_number"] == question_number:
                return entry
        return None


class InterviewMemory:
    """
    Layer 3: Structured interview state tracker.
    Tracks what topics/days have been covered, mistakes, strong areas.
    """

    def __init__(self):
        self.topics_covered: list[str] = []
        self.days_covered: list[int] = []
        self.mistakes: list[dict] = []
        self.strong_answers: list[dict] = []
        self.question_types_used: list[str] = []

    def record_answer(
        self,
        topic: str,
        curriculum_day: Optional[int],
        question_type: str,
        score: float,
        question: str,
        answer: str,
    ):
        if topic not in self.topics_covered:
            self.topics_covered.append(topic)
        if curriculum_day and curriculum_day not in self.days_covered:
            self.days_covered.append(curriculum_day)
        self.question_types_used.append(question_type)

        record = {"topic": topic, "question": question, "answer": answer, "score": score}
        if score < 0.5:
            self.mistakes.append(record)
        elif score >= 0.75:
            self.strong_answers.append(record)

    def days_remaining_needed(self, min_days: int = 4) -> int:
        return max(0, min_days - len(self.days_covered))

    def topics_not_covered(self, all_topics: list[str]) -> list[str]:
        return [t for t in all_topics if t not in self.topics_covered]

    def get_summary(self) -> dict:
        return {
            "topics_covered": self.topics_covered,
            "days_covered": self.days_covered,
            "mistake_count": len(self.mistakes),
            "strong_count": len(self.strong_answers),
            "question_types_used": list(set(self.question_types_used)),
        }


class MemoryEngine:
    """
    Combined memory engine — orchestrates all four layers.
    Each interview session gets one MemoryEngine instance.
    """

    def __init__(self):
        self.short_term = ShortTermMemory(max_size=5)
        self.reasoning = ReasoningMemory()
        self.interview = InterviewMemory()
        logger.debug("🧠 Memory Engine initialized")

    def record_qa(
        self,
        question: str,
        answer: str,
        topic: str,
        curriculum_day: Optional[int],
        question_type: str,
        score: float,
    ):
        """Record a Q&A pair across all relevant memory layers."""
        self.short_term.add(question, answer, topic, score)
        self.interview.record_answer(topic, curriculum_day, question_type, score, question, answer)

    def get_context_for_llm(self) -> str:
        """Get formatted context to inject into LLM prompts."""
        return self.short_term.to_prompt_context()

    def get_recent_topics(self) -> list[str]:
        return self.short_term.get_recent_topics()
