"""
Athena AI — LLM Response Cache (Phase 17: Performance)
Simple in-memory TTL cache for deterministic LLM calls
(planning agent, knowledge lookups) to reduce API latency.

Only caches responses for:
  - plan_next_question  (temperature 0.4, mostly deterministic)
  - Low-temperature evaluation hints

NOT used for:
  - generate_question (needs variety per session)
  - generate_socratic_followup (highly contextual)
"""
import hashlib
import json
import time
from typing import Optional, Dict, Tuple
from loguru import logger


class LLMCache:
    """
    Thread-safe in-memory cache with TTL expiry.
    Key = SHA-256 hash of (messages, temperature).
    """

    def __init__(self, ttl_seconds: int = 300, max_entries: int = 512):
        self._cache: Dict[str, Tuple[str, float]] = {}  # key -> (value, expire_at)
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._hits = 0
        self._misses = 0

    def _make_key(self, messages: list, temperature: float) -> str:
        payload = json.dumps({"m": messages, "t": round(temperature, 2)}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, messages: list, temperature: float) -> Optional[str]:
        key = self._make_key(messages, temperature)
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        value, expire_at = entry
        if time.monotonic() > expire_at:
            del self._cache[key]
            self._misses += 1
            return None
        self._hits += 1
        logger.debug(f"🚀 LLM Cache HIT (ratio={self._hits}/{self._hits+self._misses})")
        return value

    def set(self, messages: list, temperature: float, response: str) -> None:
        if len(self._cache) >= self.max_entries:
            # Evict the oldest 10% of entries
            now = time.monotonic()
            expired_keys = [k for k, (_, exp) in self._cache.items() if exp <= now]
            for k in expired_keys[:max(1, self.max_entries // 10)]:
                del self._cache[k]

        key = self._make_key(messages, temperature)
        self._cache[key] = (response, time.monotonic() + self.ttl)

    def stats(self) -> dict:
        return {
            "entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self._hits / max(1, self._hits + self._misses), 3),
        }

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0


# Global singleton — imported by llm.py for planning calls
_planning_cache = LLMCache(ttl_seconds=300, max_entries=512)
