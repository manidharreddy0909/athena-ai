"""
Athena AI — Provider-Agnostic LLM Client
Works with: OpenRouter, LM Studio, Groq, OpenAI, Anthropic (via proxy)
"""
from openai import AsyncOpenAI
from core.config import settings


def get_llm_client() -> AsyncOpenAI:
    """Get the LLM client configured from environment variables."""
    return AsyncOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
    )


def get_embedding_client() -> AsyncOpenAI:
    """Get the embedding client (may be same or different provider)."""
    return AsyncOpenAI(
        base_url=settings.EMBEDDING_BASE_URL,
        api_key=settings.EMBEDDING_API_KEY,
    )


async def chat_completion(
    messages: list,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """Simple wrapper for chat completions."""
    client = get_llm_client()
    kwargs = {
        "model": model or settings.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


async def get_embedding(text: str) -> list[float]:
    """Get embedding vector for a text string."""
    client = get_embedding_client()
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
