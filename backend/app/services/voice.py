"""Local voice pipeline for "AI protection by phone" (D-018).

Speech-to-text: faster-whisper (CTranslate2 int8, CPU) with an Albanian
fine-tune (Flutra/whisper-large-v3-turbo-sq-v2 converted to CT2) as the
primary model. Text-to-speech: Piper `sq_AL` voice, invoked as a CLI
subprocess (process boundary keeps the GPL-3 code out of our process and
the event loop free).

Everything runs on THIS machine — recordings and transcripts never leave
it, matching the local-embeddings privacy rule for documents.
"""
import asyncio
import io
import logging
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Whisper decode: sq model was fine-tuned on Albanian; for the other
# supported locales the same weights still carry base-turbo multilingual
# ability, so one loaded model serves everything (RAM budget: ~1.5 GB).
_WHISPER_LANGS = {"sq", "sr", "tr", "bs", "en", "zh", "de"}


def stt_enabled() -> bool:
    return (settings.voice_stt_model_dir / "model.bin").exists()


def tts_enabled() -> bool:
    return settings.voice_tts_model.exists() and settings.voice_piper_bin.exists()


@lru_cache(maxsize=1)
def _whisper_model():
    """Lazy singleton — loading takes seconds, so it happens on the first
    transcription, not at boot. GPU first (8x faster than CPU int8, ~1.6 GB
    VRAM for the turbo model), CPU fallback if CUDA is absent or broken."""
    from faster_whisper import WhisperModel

    model_dir = str(settings.voice_stt_model_dir)
    if settings.voice_stt_device in ("auto", "cuda"):
        try:
            model = WhisperModel(model_dir, device="cuda", compute_type="float16")
            logger.info("Loaded Whisper model from %s on CUDA", model_dir)
            return model
        except Exception:
            if settings.voice_stt_device == "cuda":
                raise
            logger.exception("CUDA Whisper failed, falling back to CPU")
    logger.info("Loading Whisper model from %s on CPU", model_dir)
    return WhisperModel(
        model_dir,
        device="cpu",
        compute_type="int8",
        cpu_threads=settings.voice_stt_threads,
    )


def _transcribe_sync(audio_bytes: bytes, language: str | None) -> dict:
    model = _whisper_model()
    lang = language if language in _WHISPER_LANGS else None
    segments, info = model.transcribe(
        io.BytesIO(audio_bytes),
        language=lang,
        vad_filter=True,
        beam_size=1,  # greedy: 2-3x faster on CPU, fine for dialogue
    )
    parts: list[dict] = []
    text_parts: list[str] = []
    for seg in segments:
        parts.append({"start": round(seg.start, 2), "end": round(seg.end, 2),
                      "text": seg.text.strip()})
        text_parts.append(seg.text.strip())
        if seg.end > settings.voice_max_audio_seconds:
            break
    return {
        "text": " ".join(text_parts).strip(),
        "language": info.language,
        "duration": round(info.duration, 2),
        "segments": parts,
    }


# One transcription at a time: the model shares CPU with the web workers
# and parallel decodes would trash both.
_stt_lock = asyncio.Lock()


async def transcribe(audio_bytes: bytes, language: str | None = None) -> dict:
    """audio_bytes: any container ffmpeg/PyAV understands (webm/opus, wav, mp4)."""
    if not stt_enabled():
        raise RuntimeError("STT model not installed (data/models/whisper-sq-ct2)")
    async with _stt_lock:
        return await asyncio.to_thread(_transcribe_sync, audio_bytes, language)


async def synthesize(text: str) -> bytes:
    """Albanian text -> WAV bytes via the Piper CLI (sq_AL voice).

    Other locales fall back to the browser's speechSynthesis on the client;
    Albanian is the one language browsers don't ship a voice for.
    """
    if not tts_enabled():
        raise RuntimeError("TTS voice not installed (data/models/piper-sq)")
    text = text.strip()[: settings.voice_max_tts_chars]
    if not text:
        raise ValueError("Empty text")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = Path(tmp.name)
    try:
        proc = await asyncio.create_subprocess_exec(
            str(settings.voice_piper_bin),
            "-m", str(settings.voice_tts_model),
            "-f", str(out_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(
            proc.communicate(text.encode()), timeout=60
        )
        if proc.returncode != 0:
            raise RuntimeError(f"piper failed: {stderr.decode()[:300]}")
        wav = out_path.read_bytes()
        if len(wav) < 100:
            raise RuntimeError("piper produced no audio")
        return wav
    finally:
        out_path.unlink(missing_ok=True)


def wav_duration_seconds(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes)) as w:
        return w.getnframes() / w.getframerate()
