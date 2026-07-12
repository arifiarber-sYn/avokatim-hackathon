"""Voice service unit tests (models optional — heavy tests skip when absent)."""
import pytest

from app.services import voice


def test_enabled_flags_reflect_model_presence():
    # On the production machine both are installed; the flags must never
    # raise regardless.
    assert isinstance(voice.stt_enabled(), bool)
    assert isinstance(voice.tts_enabled(), bool)


@pytest.mark.anyio
async def test_tts_rejects_empty_text():
    if not voice.tts_enabled():
        pytest.skip("piper voice not installed")
    with pytest.raises(ValueError):
        await voice.synthesize("   ")


@pytest.mark.anyio
async def test_tts_roundtrip_albanian():
    if not (voice.tts_enabled() and voice.stt_enabled()):
        pytest.skip("voice models not installed")
    wav = await voice.synthesize("Kjo është një provë e shkurtër.")
    assert wav[:4] == b"RIFF"
    assert voice.wav_duration_seconds(wav) > 0.5
    result = await voice.transcribe(wav, language="sq")
    assert result["language"] == "sq"
    assert "prov" in result["text"].lower()


def test_transcribe_language_whitelist():
    from app.services.voice import _WHISPER_LANGS

    assert _WHISPER_LANGS == {"sq", "sr", "tr", "bs", "en", "zh"}
