"""
Athena AI — BREATH AI Layer Client
A client to interface with the BREATH API (Persistent Reasoning Memory).
For Phase 4, if the API is down or unavailable, it degrades gracefully (mock behavior)
but is architecturally ready for production.
"""
import httpx
from typing import Dict, Any, Optional
from loguru import logger
from core.config import settings
import asyncio


class BreathMemoryClient:
    """Client to interface with the BREATH API for persistent reasoning memory."""
    
    def __init__(self):
        self.base_url = "https://api.breath.ai/v1"
        self.api_key = settings.BREATH_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # In mock mode if API key is not configured
        self.mock_mode = not bool(self.api_key)

    async def save_reasoning_trace(
        self,
        session_id: str,
        question_number: int,
        topic: str,
        reasoning_trace: Dict[str, Any]
    ) -> bool:
        """
        Push an agent reasoning trace to BREATH.
        This provides the persistent Layer 4 memory for Explainable AI.
        """
        payload = {
            "session_id": session_id,
            "event_type": "reasoning_trace",
            "metadata": {
                "question_number": question_number,
                "topic": topic
            },
            "payload": reasoning_trace,
        }

        if self.mock_mode:
            logger.debug(f"[BREATH MOCK] Saved reasoning trace for session {session_id}, Q{question_number}")
            return True

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(
                    f"{self.base_url}/memory/events",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                logger.debug(f"[BREATH] Successfully synced reasoning trace for {session_id}")
                return True
        except Exception as e:
            logger.warning(f"[BREATH] Failed to sync reasoning trace (fallback to mock). Error: {e}")
            # Graceful degradation
            return False

    async def get_session_insights(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve aggregated reasoning insights from BREATH across the session."""
        if self.mock_mode:
            return {"status": "mock", "insights": ["Candidate demonstrates strong structural thinking."]}
            
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/memory/sessions/{session_id}/insights",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"[BREATH] Failed to fetch session insights. Error: {e}")
            return None
