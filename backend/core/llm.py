"""
Athena AI — Provider-Agnostic LLM Client
Implements a factory pattern to route traffic between Primary LLM and Breath AI Layer.
"""
import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from core.config import settings
from loguru import logger


class EmptyLLMResponse(Exception):
    """Raised when the LLM returns an empty response where content was expected."""


def parse_json_response(text: str) -> Any:
    """
    Parse a JSON string returned by an LLM, tolerating markdown code fences
    and surrounding prose. LM Studio / local models often wrap JSON in
    ```json ... ``` blocks or embed it in prose.
    """
    if not text or not text.strip():
        raise EmptyLLMResponse("Empty LLM response — expected JSON")
    # Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    # If the whole string is not valid JSON, try to extract the first
    # balanced JSON object/array from surrounding prose.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Find the first '{' or '[' and the matching last '}' or ']'
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


async def chat_completion_with_retry(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
    json_schema: Optional[Dict[str, Any]] = None,
    use_breath_layer: bool = False,
    max_retries: Optional[int] = None,
) -> str:
    """
    Call chat_completion with retries on empty responses or transient errors.
    Returns the raw text response. Raises the last error if all retries fail.
    """
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
            )
            if json_mode and (not result or not result.strip()):
                raise EmptyLLMResponse("Empty LLM response — expected JSON")
            return result
        except Exception as e:  # noqa: BLE001 - retry on any provider/parse error
            last_error = e
            logger.warning(
                f"LLM call attempt {attempt + 1}/{retries + 1} failed: {e}"
            )
            if attempt < retries:
                await asyncio.sleep(settings.LLM_RETRY_DELAY_SECONDS)
    raise last_error  # type: ignore[misc]


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
        # Safety: some providers return None content with tool_calls when using json_schema
        if content is None:
            tc = response.choices[0].message.tool_calls
            if tc:
                content = tc[0].function.arguments
        return content or ""


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
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Breath AI Layer might have specialized parameters. Using standard for now.
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
    json_schema: Optional[Dict[str, Any]] = None,
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
        json_schema=json_schema,
    )


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector for a text string."""
    client = ProviderFactory.get_embedding_client()
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
