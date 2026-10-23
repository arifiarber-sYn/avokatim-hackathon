"""Telephony-KI: Ava answers a real phone number, 24/7 (D-059 F4).

Call path:  caller → sipgate SIP trunk → Asterisk (docker, --profile
telephony) → AudioSocket TCP → this gateway → local Whisper STT → the same
intake machine WhatsApp uses (classify + category questions, D-059 F5) →
Piper TTS back to the caller → CaseRequest + lawyer notification.

Everything voice stays on this machine (privacy rule §5.7); only the LLM
classification goes through the usual provider abstraction (pseudonymized
since D-059 F1).

AudioSocket protocol (github.com/CyCoreSystems/audiosocket, shipped with
Asterisk 18+): TCP frames of [1-byte kind][2-byte big-endian length]
[payload]. Kinds: 0x00 hangup, 0x01 call UUID (16 raw bytes), 0x10 audio
(16-bit signed linear, 8 kHz, mono, 20 ms = 320-byte frames, both ways),
0xff error. The dialplan links the caller's number to the UUID via
GET /api/public/phone/link before handing us the stream (loopback only).

The conversational loop (M1 + M2 of the plan):
  greet → describe (record with VAD → transcribe → classify) → up to 3
  category questions → city (unless classified) → name → confirm+hangup →
  CaseRequest + notifications, exactly like the WhatsApp flow.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import logging
import secrets
import struct
import uuid as uuidlib
import wave
from array import array
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.config import settings
from app.i18n import tr
from app.jurisdictions import country_for_phone, profile_for

logger = logging.getLogger(__name__)

# --- AudioSocket framing ---
KIND_HANGUP = 0x00
KIND_ID = 0x01
KIND_SILENCE = 0x02
KIND_AUDIO = 0x10
KIND_ERROR = 0xFF

SAMPLE_RATE = 8000
FRAME_BYTES = 320  # 20 ms of 16-bit mono at 8 kHz
FRAME_SECONDS = 0.02

# --- Voice activity detection (energy-based; good enough for phone audio) ---
VAD_RMS_THRESHOLD = 300  # int16 RMS above which a frame counts as speech
VAD_SILENCE_AFTER = 1.4  # s of silence that ends an utterance
VAD_MAX_UTTERANCE = 90.0  # s hard cap per answer
VAD_NO_SPEECH_TIMEOUT = 8.0  # s of leading silence -> reprompt

MAX_QUESTIONS = 3  # same cap as WhatsApp (CONVERSATIONAL_MAX_QUESTIONS)
MIN_DESCRIPTION_WORDS = 5


def pack_frame(kind: int, payload: bytes = b"") -> bytes:
    return struct.pack(">BH", kind, len(payload)) + payload


async def read_frame(reader: asyncio.StreamReader) -> tuple[int, bytes]:
    header = await reader.readexactly(3)
    kind, length = struct.unpack(">BH", header)
    payload = await reader.readexactly(length) if length else b""
    return kind, payload


def frame_rms(frame: bytes) -> int:
    """Root-mean-square of a 16-bit slin frame (audioop is gone in 3.13+)."""
    if not frame:
        return 0
    samples = array("h", frame[: len(frame) - (len(frame) % 2)])
    if not samples:
        return 0
    return int((sum(s * s for s in samples) / len(samples)) ** 0.5)


def slin_to_wav(slin: bytes) -> bytes:
    """Wrap raw 8 kHz slin in a WAV container for Whisper."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(slin)
    return buf.getvalue()


async def wav_to_slin8k(wav_bytes: bytes) -> bytes:
    """Resample any WAV (Piper emits 22.05 kHz) to phone slin via ffmpeg."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-loglevel", "error", "-i", "pipe:0",
        "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await asyncio.wait_for(proc.communicate(wav_bytes), timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg resample failed: {err.decode()[:200]}")
    return out


# ---------- caller identity (linked by the Asterisk dialplan) ----------


async def link_call(call_uuid: str, caller: str) -> None:
    """Store uuid -> caller number (dialplan calls this over loopback)."""
    import redis.asyncio as aioredis

    r = aioredis.from_url(settings.redis_url)
    try:
        await r.set(f"phone:link:{call_uuid}", caller, ex=3600)
    finally:
        await r.aclose()


async def caller_for(call_uuid: str) -> str | None:
    import redis.asyncio as aioredis

    r = aioredis.from_url(settings.redis_url)
    try:
        raw = await r.get(f"phone:link:{call_uuid}")
        return raw.decode() if raw else None
    finally:
        await r.aclose()


# ---------- the conversation ----------


@dataclass
class CallState:
    caller: str
    country: str
    locale: str
    description: str = ""
    category: str = "other"
    city: str | None = None
    urgency: str = "normal"
    name: str = ""
    answers: dict[str, str] = field(default_factory=dict)


class PhoneCall:
    """One call's dialog. STT/TTS/classify are injectable for tests."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        *,
        stt=None,
        tts=None,
        classify=None,
    ):
        from app.services import voice
        from app.services.wa_intake import _classify

        self.reader = reader
        self.writer = writer
        self._stt = stt or voice.transcribe
        self._tts = tts or voice.synthesize
        self._classify = classify or _classify
        self.hungup = False

    # --- audio primitives ---

    async def say(self, text: str, locale: str) -> None:
        """TTS -> 8 kHz slin -> paced 20 ms frames to Asterisk."""
        if self.hungup or not text.strip():
            return
        try:
            wav = await self._tts(text, locale)
            slin = await wav_to_slin8k(wav)
        except Exception:
            logger.exception("phone TTS failed — continuing silently")
            return
        for i in range(0, len(slin), FRAME_BYTES):
            frame = slin[i : i + FRAME_BYTES].ljust(FRAME_BYTES, b"\x00")
            self.writer.write(pack_frame(KIND_AUDIO, frame))
            await self.writer.drain()
            # Real-time pacing: Asterisk plays at 8 kHz; flooding it drops audio
            await asyncio.sleep(FRAME_SECONDS * 0.9)

    async def record_utterance(self) -> bytes:
        """Collect one utterance: wait for speech, stop after trailing
        silence. Returns raw slin (empty on hangup/timeout)."""
        collected = bytearray()
        speech_started = False
        silent_for = 0.0
        waited = 0.0
        while True:
            try:
                kind, payload = await asyncio.wait_for(
                    read_frame(self.reader), timeout=10
                )
            except (TimeoutError, asyncio.IncompleteReadError, ConnectionError):
                self.hungup = True
                break
            if kind == KIND_HANGUP:
                self.hungup = True
                break
            if kind != KIND_AUDIO:
                continue
            loud = frame_rms(payload) >= VAD_RMS_THRESHOLD
            if not speech_started:
                waited += FRAME_SECONDS
                if loud:
                    speech_started = True
                    collected.extend(payload)
                elif waited >= VAD_NO_SPEECH_TIMEOUT:
                    break  # caller said nothing -> caller gets a reprompt
                continue
            collected.extend(payload)
            silent_for = 0.0 if loud else silent_for + FRAME_SECONDS
            if silent_for >= VAD_SILENCE_AFTER:
                break
            if len(collected) / (SAMPLE_RATE * 2) >= VAD_MAX_UTTERANCE:
                break
        return bytes(collected) if speech_started else b""

    async def listen(self, locale: str) -> str:
        """One utterance -> text (local Whisper). Empty on silence/hangup."""
        slin = await self.record_utterance()
        if not slin or self.hungup:
            return ""
        try:
            result = await self._stt(slin_to_wav(slin), locale)
            return (result.get("text") or "").strip()
        except Exception:
            logger.exception("phone STT failed")
            return ""

    async def ask(self, prompt: str, locale: str, retries: int = 1) -> str:
        """Say the prompt, listen; one reprompt on silence."""
        await self.say(prompt, locale)
        for attempt in range(retries + 1):
            text = await self.listen(locale)
            if text or self.hungup:
                return text
            if attempt < retries:
                await self.say(tr(locale, "phone_repeat"), locale)
        return ""

    # --- the dialog ---

    async def run(self, caller: str) -> None:
        from app.seeds.case_intake_questions import questions_for
        from app.services.wa_intake import _parse_answer, _question_prompt

        country = country_for_phone(caller)
        profile = profile_for(country)
        locale = profile.default_locale
        state = CallState(caller=caller, country=country, locale=locale)

        await self.say(
            tr(locale, "phone_greeting", brand=profile.brand_name), locale
        )

        # 1. the case description
        description = await self.ask(tr(locale, "phone_ask_describe"), locale)
        if self.hungup or len(description.split()) < MIN_DESCRIPTION_WORDS:
            if not self.hungup:
                await self.say(tr(locale, "phone_goodbye_nothing"), locale)
            return
        state.description = description
        classified = await self._classify(description)
        state.category = classified.get("category") or "other"
        state.city = classified.get("city")
        state.urgency = classified.get("urgency") or "normal"

        # 2. category questions (same seed as web + WhatsApp, D-059 F5)
        for q in questions_for(state.category, country)[:MAX_QUESTIONS]:
            if self.hungup:
                return
            answer = await self.ask(_question_prompt(q, locale), locale, retries=0)
            if answer:
                state.answers[q["key"]] = _parse_answer(q, answer)

        # 3. city + name
        if not state.city and not self.hungup:
            state.city = (await self.ask(tr(locale, "phone_ask_city"), locale))[:120]
        if not self.hungup:
            state.name = (await self.ask(tr(locale, "phone_ask_name"), locale))[:200]

        # 4. persist + notify, then confirm — even if the caller hung up
        # mid-flow we keep what we have (description is already valuable)
        try:
            await save_phone_case(state)
        except Exception:
            logger.exception("phone intake: saving the case failed")
            if not self.hungup:
                await self.say(tr(locale, "phone_error"), locale)
            return
        if not self.hungup:
            name_part = f", {state.name}" if state.name else ""
            await self.say(
                tr(locale, "phone_confirm", name_part=name_part), locale
            )
            self.writer.write(pack_frame(KIND_HANGUP))
            with contextlib.suppress(ConnectionError):
                await self.writer.drain()


async def save_phone_case(state: CallState) -> None:
    """CaseRequest from a phone call — same downstream path as WhatsApp.
    The citizen is keyed by phone number; without an email the account is a
    stub the lawyer completes on first contact (callers are called back)."""
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import CaseRequest, CitizenUser
    from app.security import hash_password

    digits = "".join(ch for ch in state.caller if ch.isdigit()) or "unknown"
    async with SessionLocal() as db:
        citizen = (
            await db.execute(
                select(CitizenUser).where(CitizenUser.phone == state.caller[:64])
            )
        ).scalars().first()
        if citizen is None:
            citizen = CitizenUser(
                # Placeholder address in a reserved, non-routable domain —
                # phone callers rarely have/give an email on the spot
                email=f"tel-{digits}@phone.invalid",
                full_name=(state.name or f"Telefonues {digits[-4:]}")[:200],
                phone=state.caller[:64],
                password_hash=hash_password(secrets.token_urlsafe(24)),
                locale=state.locale,
                country=state.country,
                privacy_accepted_at=datetime.now(UTC),
            )
            db.add(citizen)
            await db.flush()
        elif state.name and not citizen.full_name.strip():
            citizen.full_name = state.name[:200]

        case = CaseRequest(
            citizen_id=citizen.id,
            category=state.category,
            description=state.description[:8000],
            city=(state.city or "")[:120] or None,
            country=state.country,
            locale=state.locale,
            urgency=state.urgency,
            structured_answers=state.answers or None,
        )
        db.add(case)
        await db.commit()
        case_id, category, city, country = case.id, case.category, case.city, case.country

    from app.api.marketplace import _notify_matching_lawyers
    from app.services.ops_notify import notify_ops

    try:
        await _notify_matching_lawyers(case_id, category, city, country)
    except Exception:
        logger.exception("phone intake: lawyer alert failed")
    with contextlib.suppress(Exception):
        await notify_ops(
            "rast",
            f"Rast i ri me TELEFON ({state.caller}): kategoria {category}, "
            f"qyteti {city or '-'}, urgjenca {state.urgency}.",
        )


# ---------- the TCP server ----------


async def _handle_connection(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    peer = writer.get_extra_info("peername")
    try:
        kind, payload = await asyncio.wait_for(read_frame(reader), timeout=5)
        if kind != KIND_ID or len(payload) != 16:
            logger.warning("AudioSocket: bad first frame from %s", peer)
            return
        call_uuid = str(uuidlib.UUID(bytes=payload))
        caller = await caller_for(call_uuid)
        if not caller:
            logger.warning("AudioSocket: no caller linked for %s", call_uuid)
            caller = "unknown"
        logger.info("Phone call %s from %s", call_uuid, caller)
        await PhoneCall(reader, writer).run(caller)
    except Exception:
        logger.exception("phone call handling failed")
    finally:
        with contextlib.suppress(Exception):
            writer.close()
            await writer.wait_closed()


async def serve() -> None:
    """AudioSocket listener — launched from the app lifespan when
    settings.phone_gateway_enabled is true."""
    server = await asyncio.start_server(
        _handle_connection, settings.phone_gateway_host, settings.phone_gateway_port
    )
    logger.info(
        "Phone gateway (AudioSocket) listening on %s:%s",
        settings.phone_gateway_host, settings.phone_gateway_port,
    )
    async with server:
        await server.serve_forever()
