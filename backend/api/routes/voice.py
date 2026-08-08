"""
Athena AI — Voice API Routes (Phase 7)
POST /api/v1/voice/transcribe   — Upload audio, get transcript
POST /api/v1/voice/synthesize   — Submit text, get audio bytes
GET  /api/v1/voice/status       — Check voice service status
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from loguru import logger
from core.voice_service import VoiceService
from core.config import settings


router = APIRouter()


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "Aoede"
    language: str = "en"


@router.get("/voice/status")
async def voice_status():
    """Returns whether voice features are available."""
    return {
        "voice_enabled": bool(settings.VOICE_API_KEY),
        "provider": "gemini" if settings.VOICE_API_KEY else "mock",
        "features": {
            "speech_to_text": True,
            "text_to_speech": True,
            "streaming": False,  # Phase 8 stretch
        },
        "supported_languages": ["en", "es", "fr", "de", "zh", "hi", "ar"],
    }


@router.post("/voice/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "en",
):
    """
    Accept an audio file upload (webm/wav/mp3) and return the transcript.
    Used by the frontend voice mode to convert candidate speech to text.
    """
    if not file.content_type or not any(
        file.content_type.startswith(t) for t in ["audio/", "video/webm"]
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an audio file (webm, wav, mp3)."
        )

    try:
        audio_bytes = await file.read()
        if len(audio_bytes) < 100:
            raise HTTPException(status_code=400, detail="Audio file is too small or empty.")

        transcript = await VoiceService.transcribe_audio(audio_bytes, language=language)
        logger.info(f"🎙️ Transcribed {len(audio_bytes)} bytes → {len(transcript)} chars")
        return {
            "transcript": transcript,
            "language": language,
            "duration_bytes": len(audio_bytes),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/voice/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Accept text and return audio bytes.
    Used to read Athena's questions aloud to the candidate.
    Returns audio/wav binary response.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    if len(request.text) > 1000:
        raise HTTPException(status_code=400, detail="Text too long (max 1000 characters).")

    try:
        audio_bytes = await VoiceService.synthesize_speech(
            text=request.text,
            voice=request.voice,
            language=request.language,
        )

        if not audio_bytes:
            # Voice not configured — return empty with info header
            return Response(
                content=b"",
                media_type="audio/wav",
                headers={"X-Voice-Status": "unavailable"},
            )

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=athena_speech.wav",
                "X-Voice-Status": "available",
            },
        )
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")
