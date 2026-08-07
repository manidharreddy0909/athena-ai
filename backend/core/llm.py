"""
Athena AI — Provider-Agnostic LLM Client
Implements a factory pattern to route traffic between Primary LLM and Breath AI Layer.
"""
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from core.config import settings
from loguru import logger


def parse_json_response(text: str) -> Any:
    """
    Parse a JSON string returned by an LLM, tolerating markdown code fences
    and surrounding prose. LM Studio / local models often wrap JSON in
    ```json ... ``` blocks.
    """
    if not text:
        raise ValueError("Empty LLM response — expected JSON")
    # Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    return json.loads(text)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        pass


class OpenAICompatibleProvider(AIProvider):
    """Generic provider for OpenAI, OpenRouter, LM Studio, Groq, etc."""
    
    def __init__(self, base_url: str, api_key: str, default_model: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.default_model = default_model

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        kwargs = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # NOTE: json_mode does NOT set response_format. LM Studio rejects
        # "json_object" and returns empty content for "text". The prompts
        # already instruct the model to return strict JSON, so we omit
        # response_format entirely for maximum provider compatibility.

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


class BreathAILayerProvider(AIProvider):
    """Provider specifically for the Breath AI Layer Pro API."""
    
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.default_model = "breath-reasoning-v1"  # Hypothetical default

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        # Breath AI Layer might have specialized parameters. Using standard for now.
        kwargs = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Same compatibility fix as OpenAICompatibleProvider: omit
        # response_format entirely so LM Studio returns content.
            
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


class ProviderFactory:
    """Manages provider instantiation and fallback logic."""
    
    _primary_provider: Optional[AIProvider] = None
    _breath_provider: Optional[AIProvider] = None
    _embedding_provider: Optional[AsyncOpenAI] = None

    @classmethod
    def get_primary(cls) -> AIProvider:
        if not cls._primary_provider:
            cls._primary_provider = OpenAICompatibleProvider(
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
                default_model=settings.LLM_MODEL,
            )
        return cls._primary_provider

    @classmethod
    def get_breath_layer(cls) -> AIProvider:
        """Returns Breath AI Layer if configured, otherwise falls back to Primary."""
        if settings.BREATH_AI_API_KEY and settings.BREATH_AI_BASE_URL:
            if not cls._breath_provider:
                cls._breath_provider = BreathAILayerProvider(
                    base_url=settings.BREATH_AI_BASE_URL,
                    api_key=settings.BREATH_AI_API_KEY,
                )
            return cls._breath_provider
        
        # Fallback to primary if Breath AI is not configured
        logger.debug("Breath AI Layer not configured. Falling back to Primary Provider.")
        return cls.get_primary()

    @classmethod
    def get_embedding_client(cls) -> AsyncOpenAI:
        if not cls._embedding_provider:
            cls._embedding_provider = AsyncOpenAI(
                base_url=settings.EMBEDDING_BASE_URL,
                api_key=settings.EMBEDDING_API_KEY,
            )
        return cls._embedding_provider


# ─────────────────────────────────────────────
# Convenience Wrappers for existing agents
# ─────────────────────────────────────────────

async def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
    use_breath_layer: bool = False,
) -> str:
    """Simple wrapper that routes to the appropriate provider."""
    if use_breath_layer:
        provider = ProviderFactory.get_breath_layer()
    else:
        provider = ProviderFactory.get_primary()
        
    return await provider.chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=json_mode,
    )


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector for a text string."""
    client = ProviderFactory.get_embedding_client()
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
