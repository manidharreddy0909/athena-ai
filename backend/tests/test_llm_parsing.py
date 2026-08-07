"""
Athena AI — Deterministic LLM Parsing & Fallback Tests
These tests do NOT require LM Studio. They verify the JSON parsing,
retry, and curriculum-fallback logic in isolation.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.llm import parse_json_response, EmptyLLMResponse, chat_completion_with_retry
from core.config import settings


# ─────────────────────────────────────────────
# parse_json_response tests
# ─────────────────────────────────────────────

def test_normal_json():
    """A plain JSON object parses correctly."""
    result = parse_json_response('{"score": 0.8, "feedback": "good"}')
    assert result == {"score": 0.8, "feedback": "good"}


def test_fenced_json():
    """Markdown-fenced JSON parses correctly."""
    result = parse_json_response('```json\n{"score": 0.7}\n```')
    assert result == {"score": 0.7}


def test_json_surrounded_by_prose():
    """JSON embedded in surrounding prose is extracted."""
    text = 'Here is the result: {"score": 0.6, "topic": "RAG"} Hope that helps.'
    result = parse_json_response(text)
    assert result == {"score": 0.6, "topic": "RAG"}


def test_malformed_json_raises():
    """Malformed JSON with no extractable object raises."""
    with pytest.raises(Exception):
        parse_json_response("this is not json at all")


def test_empty_response_raises():
    """Empty response raises EmptyLLMResponse."""
    with pytest.raises(EmptyLLMResponse):
        parse_json_response("")
    with pytest.raises(EmptyLLMResponse):
        parse_json_response("   \n  ")


# ─────────────────────────────────────────────
# chat_completion_with_retry tests
# ─────────────────────────────────────────────

class FakeProvider:
    """A fake provider that returns a scripted sequence of responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    async def chat_completion(self, **kwargs):
        self.calls += 1
        if not self.responses:
            raise RuntimeError("No more scripted responses")
        return self.responses.pop(0)


async def _run_retry(provider, json_mode=True, max_retries=2):
    """Run chat_completion_with_retry against a fake provider."""
    # Monkeypatch the module-level chat_completion to use our fake provider.
    import core.llm as llm_mod

    original = llm_mod.chat_completion

    async def fake_chat_completion(**kwargs):
        return await provider.chat_completion(**kwargs)

    llm_mod.chat_completion = fake_chat_completion
    try:
        return await chat_completion_with_retry(
            [{"role": "user", "content": "test"}],
            json_mode=json_mode,
            max_retries=max_retries,
        )
    finally:
        llm_mod.chat_completion = original


def test_retry_succeeds_on_second_attempt():
    """Retry succeeds when the first attempt returns empty."""
    provider = FakeProvider(["", '{"score": 0.9}'])
    result = asyncio.run(_run_retry(provider, max_retries=2))
    assert result == '{"score": 0.9}'
    assert provider.calls == 2


def test_retry_exhausts_and_raises():
    """Retry raises after all attempts return empty."""
    provider = FakeProvider(["", "", ""])
    with pytest.raises(EmptyLLMResponse):
        asyncio.run(_run_retry(provider, max_retries=2))
    assert provider.calls == 3


def test_retry_succeeds_first_attempt():
    """No retry needed when the first attempt succeeds."""
    provider = FakeProvider(['{"score": 0.5}'])
    result = asyncio.run(_run_retry(provider, max_retries=2))
    assert result == '{"score": 0.5}'
    assert provider.calls == 1


# ─────────────────────────────────────────────
# Curriculum fallback selection test
# ─────────────────────────────────────────────

def test_fallback_selects_uncovered_day():
    """The deterministic fallback picks a topic from an uncovered curriculum day."""
    from knowledge.knowledge_graph import KnowledgeGraph

    graph = KnowledgeGraph()
    # Simulate that day 1 (Prompt Engineering) is already covered.
    covered_days = [1]
    covered_topics = ["Prompt Engineering"]

    uncovered_days = sorted(
        {d for d in range(1, 26) if d not in covered_days}
    )
    fallback_topic = None
    for day in uncovered_days:
        candidates = [
            t for t in graph.get_topics_for_day(day)
            if t not in covered_topics
        ]
        if candidates:
            fallback_topic = candidates[0]
            break

    assert fallback_topic is not None
    # The selected topic must NOT be from an already-covered day.
    assert graph.get_curriculum_day(fallback_topic) not in covered_days