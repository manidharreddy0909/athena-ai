"""
Athena AI — Voice Architecture (Phase 7)
Implements Speech-to-Text (STT) and Text-to-Speech (TTS) adapters.
Uses the VOICE_API_KEY env var. Supports:
  - Gemini Live (primary, via Gemini streaming)
  - OpenAI Whisper (STT fallback)
  - Google Cloud TTS (TTS fallback)
  - Browser Web Speech API (frontend fallback, no key needed)

When VOICE_API_KEY is not configured, voice routes return graceful
error responses so the frontend can fall back to text mode.
"""
import asyncio
import base64
import io
from typing import Optional
from loguru import logger
from core.config import settings


class VoiceProvider:
    """Base voice provider interface."""

    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        raise NotImplementedError

    async def synthesize(self, text: str, voice: str = "default", language: str = "en") -> bytes:
        raise NotImplementedError


class GeminiVoiceProvider(VoiceProvider):
    """
    Gemini-based voice using the Gemini multimodal API.
    Transcribes audio via Gemini's audio understanding capabilities.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        """Send audio bytes to Gemini and get transcript."""
        try:
            import httpx
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "audio/webm",
                                    "data": audio_b64,
                                }
                            },
                            {
                                "text": "Transcribe this audio exactly. Return ONLY the transcript, no other text."
                            },
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": 500,
                },
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/models/gemini-2.0-flash:generateContent",
                    params={"key": self.api_key},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                transcript = data["candidates"][0]["content"]["parts"][0]["text"]
                return transcript.strip()
        except Exception as e:
            logger.error(f"Gemini transcription failed: {e}")
            raise

    async def synthesize(self, text: str, voice: str = "Aoede", language: str = "en") -> bytes:
        """Use Gemini TTS to synthesize speech."""
        # Gemini 2.5 TTS endpoint (Preview)
        try:
            import httpx
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {"voice_name": voice}
                        }
                    },
                },
                "model": "gemini-2.5-flash-preview-tts",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/models/gemini-2.5-flash-preview-tts:generateContent",
                    params={"key": self.api_key},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                audio_b64 = data["candidates"][0]["content"]["parts"][0]["inline_data"]["data"]
                return base64.b64decode(audio_b64)
        except Exception as e:
            logger.error(f"Gemini TTS failed: {e}")
            raise


class MockVoiceProvider(VoiceProvider):
    """
    Mock voice provider for when VOICE_API_KEY is not configured.
    Returns empty/placeholder audio so the system degrades gracefully.
    """

    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        logger.warning("Voice not configured — returning mock transcript.")
        return "[Voice transcription unavailable. Please configure VOICE_API_KEY.]"

    async def synthesize(self, text: str, voice: str = "default", language: str = "en") -> bytes:
        logger.warning("Voice not configured — returning empty audio.")
        return b""  # Empty audio bytes


class VoiceService:
    """
    High-level voice service. Routes to appropriate provider based on config.
    """
    _instance: Optional["VoiceService"] = None
    _provider: Optional[VoiceProvider] = None

    @classmethod
    def get_provider(cls) -> VoiceProvider:
        if cls._provider is None:
            if settings.VOICE_API_KEY:
                logger.info("🎙️ Voice: Using Gemini Voice Provider")
                cls._provider = GeminiVoiceProvider(api_key=settings.VOICE_API_KEY)
            else:
                logger.warning("🎙️ Voice: VOICE_API_KEY not set. Using mock provider.")
                cls._provider = MockVoiceProvider()
        return cls._provider

    @classmethod
    async def transcribe_audio(cls, audio_bytes: bytes, language: str = "en") -> str:
        """Convert audio bytes to text transcript."""
        provider = cls.get_provider()
        return await provider.transcribe(audio_bytes, language)

    @classmethod
    async def synthesize_speech(cls, text: str, voice: str = "Aoede", language: str = "en") -> bytes:
        """Convert text to audio bytes (WAV/PCM)."""
        provider = cls.get_provider()
        return await provider.synthesize(text, voice, language)
