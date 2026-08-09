"""
Athena AI — BREETH AI Persistent Memory Client
Integrates with the official `breeth` SDK to record and retrieve
candidate intelligence, strengths, weaknesses, and interview history.
"""
from typing import Dict, Any, Optional, List
from loguru import logger
from core.config import settings

# Attempt to import the official SDK
try:
    from breeth import AsyncBreethClient, BreethError
    HAS_BREETH_SDK = True
except ImportError:
    HAS_BREETH_SDK = False
    logger.warning("Breeth SDK not installed. Memory integration will run in degraded mode.")


class BreethMemoryClient:
    """
    Client for storing and retrieving candidate memory using BREETH AI.
    Gracefully degrades if the API key is not configured or the service is down.
    """
    
    def __init__(self):
        self.api_key = settings.BREETH_API_KEY
        
        self.is_configured = bool(self.api_key and HAS_BREETH_SDK)
        self.client: Optional["AsyncBreethClient"] = None
        
        if self.is_configured:
            try:
                self.client = AsyncBreethClient(api_key=self.api_key)
                logger.info("BREETH Persistent Memory Layer configured.")
            except Exception as e:
                logger.error(f"Failed to initialize BREETH Client: {e}")
                self.is_configured = False
        else:
            logger.warning("BREETH Persistent Memory Layer NOT configured. Operating in mock mode.")

    def get_status(self) -> str:
        if not HAS_BREETH_SDK:
            return "sdk_missing"
        if not self.api_key:
            return "not_configured"
        return "connected" if self.client else "initialization_failed"

    async def save_episode(self, session_id: str, candidate_name: str, content: str) -> bool:
        """
        Record a memory episode (e.g. Q&A interaction, insight, or summary) to BREETH.
        Groups by candidate name.
        """
        group_id = f"candidate_{candidate_name.lower().replace(' ', '_')}"
        
        if not self.is_configured or not self.client:
            logger.debug(f"[BREETH MOCK] Saved episode for {group_id}: {content[:50]}...")
            return False
            
        try:
            response = await self.client.write(
                content=f"[Session: {session_id}] {content}",
                group_id=group_id
            )
            logger.debug(f"[BREETH] Episode saved for {group_id}. Result: {response.ok}")
            return response.ok
        except Exception as e:
            logger.warning(f"[BREETH] Failed to save episode. Service may be unavailable: {e}")
            return False

    async def retrieve_context(self, candidate_name: str, query: str, limit: int = 5) -> List[str]:
        """
        Retrieve relevant past memories for a candidate based on a semantic query.
        Returns a list of formatted memory strings.
        """
        group_id = f"candidate_{candidate_name.lower().replace(' ', '_')}"
        
        if not self.is_configured or not self.client:
            logger.debug(f"[BREETH MOCK] Retrieve context for {group_id} - query: {query}")
            return []
            
        try:
            response = await self.client.retrieve(
                query=query,
                group_id=group_id,
                limit=limit
            )
            
            # The SDK returns a RetrieveResponse. We format the node details.
            # Assuming response.edges contains EdgeHit objects.
            memories = []
            if hasattr(response, 'edges') and response.edges:
                for edge in response.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        memories.append(edge.fact)
            
            return memories
        except Exception as e:
            logger.warning(f"[BREETH] Failed to retrieve context. Service may be unavailable: {e}")
            return []
