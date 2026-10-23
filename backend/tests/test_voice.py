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
    # CUDA greedy decode is not bit-stable on single words ("provë" can come
    # out as "proga"), so assert on the sentence frame instead.
    text = result["text"].lower()
    assert "kjo është një" in text and "shkurtër" in text


def test_transcribe_language_whitelist():
    from app.services.voice import _WHISPER_LANGS

    assert _WHISPER_LANGS == {"sq", "sr", "tr", "bs", "en", "zh", "de"}


def test_tts_languages_include_albanian_and_german():
    langs = voice.tts_languages()
    if not langs:
        pytest.skip("piper voices not installed")
    assert "sq" in langs
    assert "de" in langs  # German voice required for the DE market


@pytest.mark.anyio
async def test_tts_roundtrip_german():
    """German TTS + stock-multilingual STT — the pair the DE market uses.
    The sq fine-tune must NOT serve German (audit 2026-08-01: unusable)."""
    if not (voice.stt_enabled() and "de" in voice.tts_languages()):
        pytest.skip("voice models not installed")
    wav = await voice.synthesize(
        "Die Verjährungsfrist beträgt drei Jahre.", language="de"
    )
    assert wav[:4] == b"RIFF"
    result = await voice.transcribe(wav, language="de")
    assert result["language"] == "de"
    assert "verjährungsfrist" in result["text"].lower()
