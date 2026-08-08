"""
Athena AI — Semantic Memory (Layer 2)
Integrates with Qdrant for vector search of past Q&A history.
"""
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from loguru import logger
from core.config import settings
from core.llm import get_embedding
from typing import List, Dict, Any


class SemanticMemory:
    """Layer 2: Semantic search of past questions using Qdrant."""
    
    COLLECTION_NAME = "athena_qa_memory"

    def __init__(self):
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        )
        self.collection_initialized = False

    async def _ensure_collection(self):
        if self.collection_initialized:
            return
            
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == self.COLLECTION_NAME for c in collections.collections)
            
            if not exists:
                await self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=qdrant_models.VectorParams(
                        size=768, # Gemini embedding size (text-embedding-004 is 768)
                        distance=qdrant_models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.COLLECTION_NAME}")
            self.collection_initialized = True
        except Exception as e:
            logger.warning(f"Failed to initialize Qdrant collection (semantic search disabled): {e}")

    async def add_memory(self, session_id: str, question: str, answer: str, topic: str):
        """Embed and store a Q&A pair."""
        try:
            await self._ensure_collection()
            
            # Combine Q and A for semantic meaning
            text_to_embed = f"Question about {topic}: {question}\nAnswer: {answer}"
            vector = await get_embedding(text_to_embed)
            
            import uuid
            point_id = str(uuid.uuid4())
            
            await self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    qdrant_models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "session_id": session_id,
                            "topic": topic,
                            "question": question,
                            "answer": answer,
                        }
                    )
                ]
            )
        except Exception as e:
            logger.warning(f"Semantic memory upsert failed: {e}")

    async def search_relevant_history(self, session_id: str, current_topic: str, query_text: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Retrieve relevant past Q&A for a given session."""
        try:
            await self._ensure_collection()
            
            query_vector = await get_embedding(query_text)
            
            results = await self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="session_id",
                            match=qdrant_models.MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=limit
            )
            
            return [hit.payload for hit in results if hit.payload]
        except Exception as e:
            logger.warning(f"Semantic memory search failed: {e}")
            return []
