"""
Athena AI — Multilingual Interview System (Phase 8)
Supports interviews in English, Telugu, Hindi, Spanish, French, German,
Chinese, Arabic, and extensible language support.

Architecture:
- LanguageConfig: defines all supported languages and their metadata
- TranslationService: translates questions/feedback using Gemini
- MultilingualPromptBuilder: generates language-aware system prompts
- LanguageDetector: auto-detects candidate's preferred language

All translations use Gemini with graceful English fallback.
"""
from typing import Optional, Dict, List
from loguru import logger
from enum import Enum


class SupportedLanguage(str, Enum):
    """Supported interview languages."""
    ENGLISH = "en"
    TELUGU = "te"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    ARABIC = "ar"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    KOREAN = "ko"


LANGUAGE_METADATA: Dict[str, Dict] = {
    "en": {"name": "English", "native_name": "English", "rtl": False, "tts_voice": "Aoede"},
    "te": {"name": "Telugu", "native_name": "తెలుగు", "rtl": False, "tts_voice": "Kore"},
    "hi": {"name": "Hindi", "native_name": "हिन्दी", "rtl": False, "tts_voice": "Kore"},
    "es": {"name": "Spanish", "native_name": "Español", "rtl": False, "tts_voice": "Leda"},
    "fr": {"name": "French", "native_name": "Français", "rtl": False, "tts_voice": "Leda"},
    "de": {"name": "German", "native_name": "Deutsch", "rtl": False, "tts_voice": "Aoede"},
    "zh": {"name": "Chinese", "native_name": "中文", "rtl": False, "tts_voice": "Kore"},
    "ar": {"name": "Arabic", "native_name": "العربية", "rtl": True, "tts_voice": "Charon"},
    "pt": {"name": "Portuguese", "native_name": "Português", "rtl": False, "tts_voice": "Leda"},
    "ja": {"name": "Japanese", "native_name": "日本語", "rtl": False, "tts_voice": "Kore"},
    "ko": {"name": "Korean", "native_name": "한국어", "rtl": False, "tts_voice": "Kore"},
}


class MultilingualService:
    """
    Handles all language operations:
    - question/feedback translation
    - language-aware system prompts
    - language metadata
    """

    @staticmethod
    def get_language_info(lang_code: str) -> Dict:
        """Return metadata for a language code."""
        return LANGUAGE_METADATA.get(lang_code, LANGUAGE_METADATA["en"])

    @staticmethod
    def get_all_supported_languages() -> List[Dict]:
        """Return list of all supported languages for the frontend picker."""
        return [
            {"code": code, **meta}
            for code, meta in LANGUAGE_METADATA.items()
        ]

    @staticmethod
    def build_language_system_prompt(lang_code: str, base_prompt: str) -> str:
        """
        Wraps the base system prompt with language instructions.
        Ensures the LLM responds in the candidate's language.
        """
        if lang_code == "en":
            return base_prompt

        lang_info = LANGUAGE_METADATA.get(lang_code, LANGUAGE_METADATA["en"])
        lang_name = lang_info["name"]
        native_name = lang_info["native_name"]

        return (
            f"{base_prompt}\n\n"
            f"IMPORTANT: The candidate has selected {lang_name} ({native_name}) as their interview language. "
            f"You MUST respond entirely in {lang_name}. "
            f"Ask the question in {lang_name}. "
            f"Provide feedback in {lang_name}. "
            f"Technical terms may remain in English if no {lang_name} equivalent exists. "
            f"Be culturally sensitive and professional."
        )

    @staticmethod
    async def translate_text(
        text: str,
        target_language: str,
        context: str = "interview question",
    ) -> str:
        """
        Translate text to target language using Gemini.
        Falls back to original text on failure.
        """
        if target_language == "en" or not text.strip():
            return text

        lang_info = LANGUAGE_METADATA.get(target_language, LANGUAGE_METADATA["en"])
        lang_name = lang_info["name"]

        try:
            from core.llm import chat_completion, LogicRole
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are a professional technical translator. "
                        f"Translate the following {context} to {lang_name}. "
                        f"Preserve technical terms (like RAG, API, LLM, etc.) in English. "
                        f"Output ONLY the translated text, nothing else."
                    ),
                },
                {
                    "role": "user",
                    "content": text,
                },
            ]
            translated = await chat_completion(
                messages,
                temperature=0.1,
                max_tokens=600,
                role=LogicRole.FAST,
            )
            return translated.strip()
        except Exception as e:
            logger.warning(f"Translation to {lang_name} failed, using original: {e}")
            return text  # Graceful fallback

    @staticmethod
    async def detect_language(text: str) -> str:
        """
        Detect the language of a text string.
        Returns a language code (e.g., 'en', 'hi').
        Falls back to 'en' on failure.
        """
        if not text or len(text.strip()) < 5:
            return "en"

        try:
            from core.llm import chat_completion, LogicRole
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"Detect the language of this text: \"{text[:200]}\"\n"
                        "Return ONLY the ISO 639-1 two-letter language code (e.g., 'en', 'hi', 'te', 'es'). "
                        "Nothing else."
                    ),
                }
            ]
            result = await chat_completion(
                messages,
                temperature=0.0,
                max_tokens=5,
                role=LogicRole.FAST,
            )
            code = result.strip().lower()[:2]
            if code in LANGUAGE_METADATA:
                return code
            return "en"
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"
