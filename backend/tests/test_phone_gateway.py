"""Telephony-KI gateway (D-059 F4): AudioSocket framing, energy VAD and the
dialog flow — audio and DB faked, the state machine is real."""

import asyncio
import io
import struct
import wave
from array import array

import pytest

from app.services import phone_gateway as pg

# ---------- framing ----------


def test_pack_and_read_frame_roundtrip():
    frame = pg.pack_frame(pg.KIND_AUDIO, b"\x01\x02\x03")
    assert frame == struct.pack(">BH", 0x10, 3) + b"\x01\x02\x03"

    async def _read():
        reader = asyncio.StreamReader()
        reader.feed_data(frame + pg.pack_frame(pg.KIND_HANGUP))
        reader.feed_eof()
        first = await pg.read_frame(reader)
        second = await pg.read_frame(reader)
        return first, second

    (k1, p1), (k2, p2) = asyncio.run(_read())
    assert (k1, p1) == (pg.KIND_AUDIO, b"\x01\x02\x03")
    assert (k2, p2) == (pg.KIND_HANGUP, b"")


def _tone_frame(amplitude: int) -> bytes:
    return array("h", [amplitude, -amplitude] * (pg.FRAME_BYTES // 4)).tobytes()


def test_frame_rms_separates_speech_from_silence():
    assert pg.frame_rms(b"\x00" * pg.FRAME_BYTES) == 0
    assert pg.frame_rms(_tone_frame(3000)) > pg.VAD_RMS_THRESHOLD
    assert pg.frame_rms(_tone_frame(50)) < pg.VAD_RMS_THRESHOLD


def test_slin_to_wav_is_8k_mono_16bit():
    slin = _tone_frame(1000) * 10
    with wave.open(io.BytesIO(pg.slin_to_wav(slin))) as w:
        assert w.getframerate() == pg.SAMPLE_RATE
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.readframes(w.getnframes()) == slin


# ---------- VAD recording ----------


def _feed(reader: asyncio.StreamReader, *frames: bytes) -> None:
    for f in frames:
        reader.feed_data(pg.pack_frame(pg.KIND_AUDIO, f))


class _NullWriter:
    def write(self, data):  # pragma: no cover - not exercised in VAD tests
        pass

    async def drain(self):
        pass


@pytest.mark.anyio
async def test_record_utterance_stops_after_trailing_silence():
    reader = asyncio.StreamReader()
    silence = b"\x00" * pg.FRAME_BYTES
    speech = _tone_frame(3000)
    _feed(reader, *([silence] * 5), *([speech] * 20))
    trailing = int(pg.VAD_SILENCE_AFTER / pg.FRAME_SECONDS) + 2
    _feed(reader, *([silence] * trailing))

    call = pg.PhoneCall(reader, _NullWriter(), stt=lambda *a: None,
                        tts=lambda *a: None, classify=lambda *a: None)
    slin = await call.record_utterance()
    assert len(slin) >= 20 * pg.FRAME_BYTES  # all speech frames captured
    assert not call.hungup


@pytest.mark.anyio
async def test_record_utterance_hangup_mid_speech():
    reader = asyncio.StreamReader()
    _feed(reader, _tone_frame(3000))
    reader.feed_data(pg.pack_frame(pg.KIND_HANGUP))

    call = pg.PhoneCall(reader, _NullWriter(), stt=lambda *a: None,
                        tts=lambda *a: None, classify=lambda *a: None)
    await call.record_utterance()
    assert call.hungup


# ---------- the dialog ----------


class _ScriptedCall(pg.PhoneCall):
    """Dialog test double: listen() replays a script, say() records prompts."""

    def __init__(self, script: list[str], classify):
        self.script = list(script)
        self.said: list[str] = []
        self.hungup = False
        self._classify = classify
        self.writer = _NullWriter()

    async def say(self, text: str, locale: str) -> None:
        self.said.append(text)

    async def listen(self, locale: str) -> str:
        return self.script.pop(0) if self.script else ""


@pytest.mark.anyio
async def test_dialog_creates_case_with_questions(monkeypatch):
    saved: list[pg.CallState] = []

    async def fake_save(state):
        saved.append(state)

    monkeypatch.setattr(pg, "save_phone_case", fake_save)

    async def classify(text):
        return {"category": "labor", "city": None, "urgency": "normal"}

    call = _ScriptedCall(
        script=[
            "Mich hat der Arbeitgeber gestern fristlos gekündigt ohne Grund",
            "1. Juli 2026",   # termination_date
            "über 50",         # employer_size (free text kept)
            "ja",              # written_contract -> yes
            "Berlin",          # city
            "Max Mustermann",  # name
        ],
        classify=classify,
    )
    await call.run("4915112345678")

    assert len(saved) == 1
    state = saved[0]
    assert state.country == "DE"
    assert state.locale == "de"
    assert state.category == "labor"
    assert state.city == "Berlin"
    assert state.name == "Max Mustermann"
    assert state.answers["written_contract"] == "yes"
    assert state.answers["termination_date"] == "1. Juli 2026"
    # greeting + describe + 3 questions + city + name + confirm
    assert len(call.said) == 8
    assert "Ava Legal" in call.said[0]


@pytest.mark.anyio
async def test_dialog_too_short_description_no_case(monkeypatch):
    saved = []

    async def fake_save(state):
        saved.append(state)

    monkeypatch.setattr(pg, "save_phone_case", fake_save)

    async def classify(text):  # pragma: no cover - never reached
        raise AssertionError("classify must not run")

    call = _ScriptedCall(script=["hallo", "", ""], classify=classify)
    await call.run("4915112345678")
    assert saved == []
    # greeting + describe prompt + goodbye
    assert len(call.said) == 3


@pytest.mark.anyio
async def test_dialog_kosovo_number_speaks_albanian(monkeypatch):
    saved = []

    async def fake_save(state):
        saved.append(state)

    monkeypatch.setattr(pg, "save_phone_case", fake_save)

    async def classify(text):
        return {"category": "other", "city": "Prishtinë", "urgency": "urgent"}

    call = _ScriptedCall(
        script=[
            "Dua të padis kompaninë e sigurimeve sepse nuk po ma paguan dëmin",
            "Arben Krasniqi",
        ],
        classify=classify,
    )
    await call.run("38344123456")
    assert saved[0].country == "XK"
    assert saved[0].locale == "sq"
    assert saved[0].urgency == "urgent"
    assert saved[0].city == "Prishtinë"  # from classification, not asked
    assert "AvokatIM" in call.said[0]
