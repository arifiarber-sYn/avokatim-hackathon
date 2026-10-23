"""WhatsApp 24/7 receptionist (D-054 F4, localized in D-055).

Turns the Q&A bot into a full intake channel: a guided flow that ends with
a structured case on the marketplace, lawyer alerts, and free consultation
slots offered right in the chat. RDG/BRAO-safe: the bot declares it is AI,
gives information only, and every case is handled by a verified lawyer.

Country and language come from the sender's phone prefix (+49 → DE/de,
+383 → XK/sq); all replies go through the backend i18n catalog (wa_* keys)
and links point to the sender's country host.

State machine per phone number, kept in Redis (1h TTL):
    describe → [category questions ×≤3 (D-059 F5)] → city → name → email → done
Commands: RAST / FALL / CASE / SLUCAJ / DAVA start intake, ANULO / CANCEL /
ABBRECHEN / OTKAZI / IPTAL / STOP aborts.
"""
import json
import logging
import re
import secrets
from datetime import UTC, datetime

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.i18n import tr
from app.jurisdictions import country_for_phone, profile_for, public_base_url_for
from app.models import CaseRequest, CitizenUser, LawyerProfile, Tenant, User
from app.security import hash_password
from app.seeds.case_intake_questions import (
    CONVERSATIONAL_MAX_QUESTIONS,
    questions_for,
)

logger = logging.getLogger(__name__)

STATE_TTL = 3600
_START_WORDS = {"rast", "rasti", "fall", "case", "slucaj", "slučaj", "dava"}
_CANCEL_WORDS = {"anulo", "cancel", "abbrechen", "otkazi", "otkaži", "iptal", "stop"}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

MIN_DESCRIPTION = 30


def sender_country_locale(phone: str) -> tuple[str, str]:
    """(country, locale) for a WhatsApp sender, from the phone prefix."""
    country = country_for_phone(phone)
    return country, profile_for(country).default_locale


async def _get_state(r: aioredis.Redis, phone: str) -> dict | None:
    raw = await r.get(f"wa:intake:{phone}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


async def _set_state(r: aioredis.Redis, phone: str, state: dict | None) -> None:
    key = f"wa:intake:{phone}"
    if state is None:
        await r.delete(key)
    else:
        await r.set(key, json.dumps(state), ex=STATE_TTL)


async def _classify(description: str) -> dict:
    """Best-effort LLM classification (category/city/urgency); safe fallback.
    The prompt is English on purpose — case descriptions arrive in any of
    the platform languages."""
    from app.llm import get_provider
    from app.llm.base import ChatMessage

    prompt = (
        "Classify the legal case below (it may be written in any language). "
        "Return ONLY JSON:\n"
        '{"category": "civil|criminal|family|commercial|labor|administrative|other", '
        '"city": "the city if mentioned, else null", '
        '"urgency": "normal|urgent"}\n\nCASE:\n' + description[:4000]
    )
    try:
        provider = get_provider(None, purpose="json")
        result = await provider.chat([ChatMessage(role="user", content=prompt)])
        match = re.search(r"\{.*\}", result.content, re.DOTALL)
        data = json.loads(match.group(0)) if match else {}
    except Exception as exc:
        logger.info("WA intake classify failed (%s) — defaults", exc)
        data = {}
    return {
        "category": data.get("category") or "other",
        "city": data.get("city"),
        "urgency": data.get("urgency") if data.get("urgency") in ("normal", "urgent") else "normal",
    }


def _pending_questions(category: str, country: str) -> list[dict]:
    """Up to CONVERSATIONAL_MAX_QUESTIONS category questions for the chat
    flow (D-059 F5) — same seed the web form uses."""
    return questions_for(category, country)[:CONVERSATIONAL_MAX_QUESTIONS]


def _question_prompt(q: dict, locale: str) -> str:
    """One chat message per question; choices become a numbered list."""
    label = q["label"].get(locale) or q["label"]["sq"]
    if q.get("choices"):
        options = "\n".join(
            f"{i}) {c['label'].get(locale) or c['label']['sq']}"
            for i, c in enumerate(q["choices"], 1)
        )
        return f"{label}\n{options}"
    return label


def _parse_answer(q: dict, text: str) -> str:
    """A choice answered by number or by (localized) text maps to the stable
    choice value; anything else is kept as free text."""
    answer = text.strip()[:300]
    choices = q.get("choices")
    if not choices:
        return answer
    if answer.isdigit() and 1 <= int(answer) <= len(choices):
        return choices[int(answer) - 1]["value"]
    lowered = answer.lower()
    for c in choices:
        if lowered == c["value"] or lowered in {
            label.lower() for label in c["label"].values()
        }:
            return c["value"]
    return answer


async def _free_slot_lines(
    db: AsyncSession, country: str, limit_lawyers: int = 3
) -> list[str]:
    """Up to 3 bookable lawyers of the sender's country with their next free
    slot — the booking offer that closes the intake loop."""
    from app.api.bookings import _free_slots, _taken_starts

    rows = (
        await db.execute(
            select(LawyerProfile, User.full_name)
            .join(User, User.id == LawyerProfile.user_id)
            .join(Tenant, Tenant.id == LawyerProfile.tenant_id)
            .where(
                LawyerProfile.is_visible.is_(True),
                LawyerProfile.verification_status == "verified",
                LawyerProfile.booking_windows.is_not(None),
                Tenant.status == "active",
                Tenant.country == country,
            )
            .limit(20)
        )
    ).all()
    lines: list[str] = []
    for profile, name in rows:
        if not profile.booking_windows:
            continue
        try:
            taken = await _taken_starts(db, profile.tenant_id)
            slots = _free_slots(profile, taken)
        except Exception:
            continue
        if not slots:
            continue
        lines.append(f"• {name}: {slots[0]:%d.%m %H:%M}")
        if len(lines) >= limit_lawyers:
            break
    return lines


async def _finish_intake(phone: str, state: dict) -> str:
    """Create (or reuse) the citizen account, post the structured case,
    alert matching lawyers, and offer consultation slots."""
    from app.api.marketplace import _notify_matching_lawyers

    country = state.get("country") or "XK"
    locale = state.get("locale") or "sq"
    base_url = public_base_url_for(country)

    async with SessionLocal() as db:
        email = state["email"].lower()
        citizen = (
            await db.execute(select(CitizenUser).where(CitizenUser.email == email))
        ).scalar_one_or_none()
        if citizen is None:
            citizen = CitizenUser(
                email=email,
                full_name=state["name"][:200],
                phone=phone[:64],
                password_hash=hash_password(secrets.token_urlsafe(24)),
                locale=locale,
                country=country,
                privacy_accepted_at=datetime.now(UTC),
            )
            db.add(citizen)
            await db.flush()

        case = CaseRequest(
            citizen_id=citizen.id,
            category=state.get("category") or "other",
            description=state["description"][:8000],
            city=(state.get("city") or "")[:120] or None,
            country=citizen.country,
            locale=citizen.locale,
            urgency=state.get("urgency") or "normal",
            # Questionnaire answers (D-059 F5) — keys come from the seed, so
            # they are valid by construction
            structured_answers=state.get("answers") or None,
        )
        db.add(case)
        await db.commit()

        slot_lines = await _free_slot_lines(db, case.country)

    # Alert the supply side exactly like a web-posted case
    try:
        await _notify_matching_lawyers(case.id, case.category, case.city, case.country)
    except Exception as exc:
        logger.warning("WA intake lawyer alert failed: %s", exc)

    reply = tr(locale, "wa_done", url=base_url, email=email)
    if slot_lines:
        reply += tr(locale, "wa_slots", slots="\n".join(slot_lines), url=base_url)
    return reply


async def handle_intake_message(phone: str, text: str) -> str | None:
    """Advance the intake state machine. Returns the reply to send, or
    None when the message is not part of an intake (normal Q&A applies)."""
    country, locale = sender_country_locale(phone)
    r = aioredis.from_url(settings.redis_url)
    try:
        lowered = text.strip().lower()
        state = await _get_state(r, phone)

        if lowered in _CANCEL_WORDS:
            if state:
                await _set_state(r, phone, None)
                return tr(state.get("locale") or locale, "wa_cancelled")
            return None

        if state is None:
            if lowered in _START_WORDS:
                await _set_state(
                    r, phone, {"step": "describe", "country": country, "locale": locale}
                )
                return tr(locale, "wa_start")
            return None

        locale = state.get("locale") or locale
        step = state.get("step")

        def _after_questions() -> str:
            """Next prompt once the questionnaire (if any) is exhausted."""
            if state.get("city"):
                state["step"] = "name"
                return tr(locale, "wa_ask_name")
            state["step"] = "city"
            return tr(locale, "wa_ask_city")

        if step == "describe":
            if len(text.strip()) < MIN_DESCRIPTION:
                return tr(locale, "wa_too_short")
            state["description"] = text.strip()
            state.update(await _classify(text))
            # Category questionnaire (D-059 F5): up to 3 targeted questions
            # before the generic city/name/email tail
            pending = _pending_questions(
                state.get("category") or "other", state.get("country") or country
            )
            if pending:
                state["step"] = "question"
                state["q_idx"] = 0
                state["answers"] = {}
                await _set_state(r, phone, state)
                return _question_prompt(pending[0], locale)
            reply = _after_questions()
            await _set_state(r, phone, state)
            return reply

        if step == "question":
            pending = _pending_questions(
                state.get("category") or "other", state.get("country") or country
            )
            idx = int(state.get("q_idx") or 0)
            if idx < len(pending):
                answers = state.get("answers") or {}
                answers[pending[idx]["key"]] = _parse_answer(pending[idx], text)
                state["answers"] = answers
            idx += 1
            if idx < len(pending):
                state["q_idx"] = idx
                await _set_state(r, phone, state)
                return _question_prompt(pending[idx], locale)
            reply = _after_questions()
            await _set_state(r, phone, state)
            return reply

        if step == "city":
            state["city"] = text.strip()[:120]
            state["step"] = "name"
            await _set_state(r, phone, state)
            return tr(locale, "wa_ask_name")

        if step == "name":
            state["name"] = text.strip()[:200]
            state["step"] = "email"
            await _set_state(r, phone, state)
            return tr(locale, "wa_ask_email")

        if step == "email":
            candidate = text.strip()
            if not _EMAIL_RE.match(candidate):
                return tr(locale, "wa_bad_email")
            state["email"] = candidate
            await _set_state(r, phone, None)
            try:
                return await _finish_intake(phone, state)
            except Exception as exc:
                logger.exception("WA intake finish failed: %s", exc)
                return tr(
                    locale, "wa_error",
                    url=public_base_url_for(state.get("country") or country),
                )

        # Unknown step — reset defensively
        await _set_state(r, phone, None)
        return None
    finally:
        await r.aclose()


async def daily_hint(r_url: str, phone: str, locale: str = "sq") -> str:
    """The intake-keyword hint, appended at most once per day per phone."""
    try:
        r = aioredis.from_url(r_url)
        first = await r.set(f"wa:hint:{phone}", "1", nx=True, ex=24 * 3600)
        await r.aclose()
        return tr(locale, "wa_hint") if first else ""
    except Exception:
        return ""
