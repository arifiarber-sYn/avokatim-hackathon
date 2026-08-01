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
from app.security import decode_token
from app.services import voice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/voice", tags=["voice"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # ~2 min of opus with headroom


@router.get("/status")
async def voice_status():
    return {"stt": voice.stt_enabled(), "tts": voice.tts_enabled()}


def _staff_sub(request: Request) -> str | None:
    """Signed staff (lawyer/office) JWT in the same Authorization header —
    good enough for rate-limit tiering, no DB round-trip needed."""
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        payload = decode_token(auth[7:])
    except Exception:
        return None
    return payload.get("sub") if not payload.get("pre_2fa") else None


def _voice_rl_key(citizen: CitizenUser | None, request: Request) -> tuple[str, bool]:
    """(rate-limit key, is_authenticated). Citizens and logged-in lawyers get
    the higher allowance; anonymous visitors share the small per-IP one."""
    if citizen is not None:
        return f"cit:{citizen.id}", True
    staff = _staff_sub(request)
    if staff is not None:
        return f"usr:{staff}", True
    return f"ip:{_ip(request)}", False


@router.post("/transcribe")
async def transcribe_audio(
    request: Request,
    audio: UploadFile = File(...),
    language: str | None = Form(default=None),
    citizen: CitizenUser | None = Depends(_optional_citizen),
):
    """Audio (webm/opus, wav, mp4...) -> text. Anonymous callers get a small
    allowance so the SOS screen works before login; citizens and lawyers more."""
    key, authed = _voice_rl_key(citizen, request)
    await _rate_limit("voice_stt", key, limit=60 if authed else 10,
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
    key, authed = _voice_rl_key(citizen, request)
    await _rate_limit("voice_tts", key, limit=120 if authed else 20,
                      window_seconds=3600)
    if not voice.tts_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "TTS not installed")
    try:
        wav = await voice.synthesize(body.text)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    return Response(content=wav, media_type="audio/wav",
                    headers={"Cache-Control": "no-store"})
