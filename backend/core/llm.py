"""
Athena AI — Provider-Agnostic LLM Client (Phase 3: Provider Abstraction)
Implements a factory pattern to route traffic between Primary LLM and Breath AI Layer.
Supports dynamic model selection via ModelRegistry.
"""
import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from core.config import settings
from loguru import logger
from enum import Enum


class EmptyLLMResponse(Exception):
    """Raised when the LLM returns an empty response where content was expected."""


def parse_json_response(text: str) -> Any:
    """Parse a JSON string returned by an LLM, tolerating markdown code fences."""
    if not text or not text.strip():
        raise EmptyLLMResponse("Empty LLM response — expected JSON")
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = min(
            [i for i in (text.find("{"), text.find("[")) if i != -1],
            default=-1,
        )
        if start == -1:
            raise
        end_char = "}" if text[start] == "{" else "]"
        end = text.rfind(end_char)
        if end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


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
        json_schema: Optional[Dict[str, Any]] = None,
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
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        kwargs = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode and json_schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response_schema",
                    "strict": True,
                    "schema": json_schema,
                },
            }

        response = await self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        if content is None:
            tc = response.choices[0].message.tool_calls
            if tc:
                content = tc[0].function.arguments
        return content or ""


class GeminiProvider(OpenAICompatibleProvider):
    """Provider specifically for Google Gemini models."""
    def __init__(self, api_key: str, default_model: str = "gemini-2.5-flash"):
        super().__init__(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
            default_model=default_model
        )


class ClaudeProvider(OpenAICompatibleProvider):
    """Provider specifically for Anthropic Claude models (via OpenAI wrapper or direct)."""
    def __init__(self, api_key: str, default_model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(
            base_url="https://api.anthropic.com/v1/messages", # Simplified for now
            api_key=api_key,
            default_model=default_model
        )


class LocalProvider(OpenAICompatibleProvider):
    """Provider specifically for local models (LM Studio/Ollama)."""
    def __init__(self, base_url: str = "http://localhost:1234/v1", default_model: str = "gemma-4"):
        super().__init__(
            base_url=base_url,
            api_key="local",
            default_model=default_model
        )


class BreathAILayerProvider(OpenAICompatibleProvider):
    """Provider specifically for the Breath AI Layer Pro API."""
    def __init__(self, api_key: str):
        super().__init__(
            base_url="https://api.breath.ai/v1",
            api_key=api_key,
            default_model="breath-reasoning-v1"
        )


# ─────────────────────────────────────────────
# Model Registry (Role -> Provider/Model mapping)
# ─────────────────────────────────────────────
class LogicRole(str, Enum):
    FAST = "FAST"
    BALANCED = "BALANCED"
    DEEP_REASONING = "DEEP_REASONING"
    CODING = "CODING"
    INTERVIEWER = "INTERVIEWER"
    EVALUATOR = "EVALUATOR"
    REPORTER = "REPORTER"
    RESEARCH = "RESEARCH"


class ModelRegistry:
    """Maps logical roles to the appropriate provider and model based on configuration."""
    
    @classmethod
    def get_provider_and_model(cls, role: LogicRole) -> tuple[AIProvider, str]:
        # Under the strict 3-API key architecture, everything defaults to Gemini.
        # This architecture can be extended dynamically.
        gemini_provider = GeminiProvider(api_key=settings.GEMINI_API_KEY)
        
        # Role mappings
        mapping = {
            LogicRole.FAST: (gemini_provider, "gemini-2.5-flash-8b"),
            LogicRole.BALANCED: (gemini_provider, "gemini-2.5-flash"),
            LogicRole.DEEP_REASONING: (gemini_provider, "gemini-2.5-pro"),
            LogicRole.CODING: (gemini_provider, "gemini-2.5-pro"),
            LogicRole.INTERVIEWER: (gemini_provider, "gemini-2.5-flash"),
            LogicRole.EVALUATOR: (gemini_provider, "gemini-2.5-flash"),
            LogicRole.REPORTER: (gemini_provider, "gemini-2.5-pro"),
            LogicRole.RESEARCH: (gemini_provider, "gemini-2.5-pro"),
        }
        return mapping.get(role, (gemini_provider, "gemini-2.5-flash"))


class ProviderFactory:
    """Manages provider instantiation and fallback logic."""
    
    _breath_provider: Optional[AIProvider] = None
    _embedding_provider: Optional[AsyncOpenAI] = None

    @classmethod
    def get_primary(cls) -> AIProvider:
        # Defaults to the standard BALANCED role
        provider, _ = ModelRegistry.get_provider_and_model(LogicRole.BALANCED)
        return provider

    @classmethod
    def get_breath_layer(cls) -> AIProvider:
        """Returns Breath AI Layer if configured, otherwise falls back to Primary."""
        if settings.BREATH_API_KEY:
            if not cls._breath_provider:
                cls._breath_provider = BreathAILayerProvider(api_key=settings.BREATH_API_KEY)
            return cls._breath_provider
        
        logger.debug("Breath AI Layer not configured. Falling back to Primary Provider.")
        return cls.get_primary()

    @classmethod
    def get_embedding_client(cls) -> AsyncOpenAI:
        if not cls._embedding_provider:
            cls._embedding_provider = AsyncOpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=settings.GEMINI_API_KEY,
            )
        return cls._embedding_provider


async def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
    json_schema: Optional[Dict[str, Any]] = None,
    use_breath_layer: bool = False,
    role: Optional[LogicRole] = None,
) -> str:
    """Simple wrapper that routes to the appropriate provider."""
    
    if use_breath_layer:
        provider = ProviderFactory.get_breath_layer()
        active_model = model
    else:
        if role:
            provider, active_model = ModelRegistry.get_provider_and_model(role)
        else:
            provider = ProviderFactory.get_primary()
            active_model = model
            
    return await provider.chat_completion(
        messages=messages,
        model=active_model,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=json_mode,
        json_schema=json_schema,
    )


async def chat_completion_with_retry(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
    json_schema: Optional[Dict[str, Any]] = None,
    use_breath_layer: bool = False,
    max_retries: Optional[int] = None,
    role: Optional[LogicRole] = None,
) -> str:
    """Call chat_completion with retries on empty responses or transient errors."""
    retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            result = await chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                json_schema=json_schema,
                use_breath_layer=use_breath_layer,
                role=role,
            )
            if json_mode and (not result or not result.strip()):
                raise EmptyLLMResponse("Empty LLM response — expected JSON")
            return result
        except Exception as e:
            last_error = e
            logger.warning(f"LLM call attempt {attempt + 1}/{retries + 1} failed: {e}")
            if attempt < retries:
                await asyncio.sleep(settings.LLM_RETRY_DELAY_SECONDS)
    raise last_error


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector for a text string."""
    client = ProviderFactory.get_embedding_client()
    response = await client.embeddings.create(
        model="text-embedding-004",
        input=text,
    )
    return response.data[0].embedding
