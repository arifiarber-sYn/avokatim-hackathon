"""Public voice endpoints: local Albanian STT/TTS for citizens (D-018).

Free like public Ava but rate-limited hard — audio processing is the most
expensive thing this machine does per request.
"""
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.marketplace import _ip, _optional_citizen, _rate_limit
from app.models import CitizenUser
from app.services import voice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/voice", tags=["voice"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # ~2 min of opus with headroom


@router.get("/status")
async def voice_status():
    return {"stt": voice.stt_enabled(), "tts": voice.tts_enabled()}


def _voice_rl_key(citizen: CitizenUser | None, request: Request) -> str:
    return f"cit:{citizen.id}" if citizen is not None else f"ip:{_ip(request)}"


@router.post("/transcribe")
async def transcribe_audio(
    request: Request,
    audio: UploadFile = File(...),
    language: str | None = Form(default=None),
    citizen: CitizenUser | None = Depends(_optional_citizen),
):
    """Audio (webm/opus, wav, mp4...) -> text. Anonymous callers get a small
    allowance so the SOS screen works before login; citizens get more."""
    limit = 60 if citizen is not None else 10
    await _rate_limit("voice_stt", _voice_rl_key(citizen, request), limit=limit,
                      window_seconds=3600)
    if not voice.stt_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "STT not installed")
    data = await audio.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Audio too large")
    if len(data) < 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty audio")
    try:
        result = await voice.transcribe(data, language=language)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    except Exception:
        logger.exception("transcription failed")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not decode audio")
    return result


class TtsIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@router.post("/tts")
async def text_to_speech(
    body: TtsIn,
    request: Request,
    citizen: CitizenUser | None = Depends(_optional_citizen),
):
    """Albanian text -> WAV. Non-Albanian locales use the browser's own
    speechSynthesis client-side, so this endpoint is sq-only by design."""
    limit = 120 if citizen is not None else 20
    await _rate_limit("voice_tts", _voice_rl_key(citizen, request), limit=limit,
                      window_seconds=3600)
    if not voice.tts_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "TTS not installed")
    try:
        wav = await voice.synthesize(body.text)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    return Response(content=wav, media_type="audio/wav",
                    headers={"Cache-Control": "no-store"})
