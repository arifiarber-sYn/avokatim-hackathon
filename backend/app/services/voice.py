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

# Whisper decode languages we accept from clients. Albanian goes to the
# sq fine-tune; everything else (and auto-detect) goes to the stock
# multilingual model — the fine-tune badly degrades non-Albanian speech
# (audit 2026-08-01: German came out unusable).
_WHISPER_LANGS = {"sq", "sr", "tr", "bs", "en", "zh", "de"}


def stt_enabled() -> bool:
    return (settings.voice_stt_model_dir / "model.bin").exists()


def _voice_path(language: str) -> Path | None:
    """Piper voice for a language: sq uses the dedicated model, the rest
    live as {lang}.onnx in voice_tts_voices_dir."""
    if language == "sq":
        return settings.voice_tts_model if settings.voice_tts_model.exists() else None
    p = settings.voice_tts_voices_dir / f"{language}.onnx"
    return p if p.exists() else None


def tts_languages() -> list[str]:
    """Locales the server can speak (Piper voice present)."""
    if not settings.voice_piper_bin.exists():
        return []
    langs = ["sq"] if settings.voice_tts_model.exists() else []
    if settings.voice_tts_voices_dir.is_dir():
        langs += sorted(p.stem for p in settings.voice_tts_voices_dir.glob("*.onnx"))
    return langs


def tts_enabled() -> bool:
    return bool(tts_languages())


@lru_cache(maxsize=2)
def _whisper_model(which: str):
    """Lazy singletons (sq fine-tune + stock multilingual) — loading takes
    seconds, so it happens on the first transcription, not at boot. GPU
    first (8x faster than CPU int8, ~1.6 GB VRAM per turbo model), CPU
    fallback if CUDA is absent or broken."""
    from faster_whisper import WhisperModel

    if which == "sq":
        source = str(settings.voice_stt_model_dir)
        kwargs = {}
    else:
        source = settings.voice_stt_fallback_model
        kwargs = {"download_root": str(settings.voice_stt_cache_dir)}
    if settings.voice_stt_device in ("auto", "cuda"):
        try:
            model = WhisperModel(source, device="cuda", compute_type="float16", **kwargs)
            logger.info("Loaded Whisper model %s on CUDA", source)
            return model
        except Exception:
            if settings.voice_stt_device == "cuda":
                raise
            logger.exception("CUDA Whisper failed, falling back to CPU")
    logger.info("Loading Whisper model %s on CPU", source)
    return WhisperModel(
        source,
        device="cpu",
        compute_type="int8",
        cpu_threads=settings.voice_stt_threads,
        **kwargs,
    )


def _transcribe_sync(audio_bytes: bytes, language: str | None) -> dict:
    lang = language if language in _WHISPER_LANGS else None
    which = "sq" if lang == "sq" or not settings.voice_stt_fallback_model else "multi"
    model = _whisper_model(which)
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


async def synthesize(text: str, language: str = "sq") -> bytes:
    """Text -> WAV bytes via the Piper CLI, voice picked per language
    (sq_AL-edon plus the {lang}.onnx voices in voice_tts_voices_dir).

    Locales without a downloaded voice fall back to the browser's
    speechSynthesis on the client.
    """
    voice_path = _voice_path(language)
    if voice_path is None or not settings.voice_piper_bin.exists():
        raise RuntimeError(f"TTS voice for '{language}' not installed")
    text = text.strip()[: settings.voice_max_tts_chars]
    if not text:
        raise ValueError("Empty text")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = Path(tmp.name)
    try:
        proc = await asyncio.create_subprocess_exec(
            str(settings.voice_piper_bin),
            "-m", str(voice_path),
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
