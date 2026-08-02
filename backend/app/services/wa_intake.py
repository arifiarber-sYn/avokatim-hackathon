"""WhatsApp 24/7 receptionist (D-054 F4).

Turns the Q&A bot into a full intake channel: a guided flow that ends with
a structured case on the marketplace, lawyer alerts, and free consultation
slots offered right in the chat. RDG/BRAO-safe: the bot declares it is AI,
gives information only, and every case is handled by a verified lawyer.

State machine per phone number, kept in Redis (1h TTL):
    describe → city → name → email → done
Commands: RAST / FALL / CASE start intake, ANULO / CANCEL aborts.
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
from app.models import CaseRequest, CitizenUser, LawyerProfile, Tenant, User
from app.security import hash_password

logger = logging.getLogger(__name__)

STATE_TTL = 3600
_START_WORDS = {"rast", "fall", "case", "rasti"}
_CANCEL_WORDS = {"anulo", "cancel", "abbrechen", "stop"}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

MIN_DESCRIPTION = 30

MSG = {
    "start": (
        "Në rregull! Do të t'i bëj disa pyetje të shkurtra dhe rasti yt "
        "shkon te avokatët e verifikuar — falas dhe pa detyrime.\n\n"
        "ℹ Unë jam asistente AI, jo avokate; rastin do ta trajtojë "
        "gjithmonë një avokat i licencuar.\n\n"
        "1/4 — Përshkruaje çfarë ka ndodhur: kur, ku, dhe çfarë kërkon."
    ),
    "too_short": "Më duhen pak më shumë detaje që avokati ta kuptojë rastin. Shkruaj çfarë ndodhi, kur dhe ku.",
    "ask_city": "2/4 — Në cilin qytet ka ndodhur / ku jeton?",
    "ask_name": "3/4 — Emri dhe mbiemri yt?",
    "ask_email": "4/4 — Email-i yt? (aty ndjek rastin dhe përgjigjet e avokatëve)",
    "bad_email": "Ky email s'duket i saktë — provo përsëri (p.sh. emri@gmail.com).",
    "cancelled": "Në rregull, e anulova. Mund të më pyesësh çfarëdo për ligjet, ose shkruaj RAST kur të duash.",
    "hint": "\n\n💡 Shkruaj RAST për ta dërguar rastin tënd te avokatët e verifikuar — falas.",
}


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
    """Best-effort LLM classification (category/city/urgency); safe fallback."""
    from app.llm import get_provider
    from app.llm.base import ChatMessage

    prompt = (
        "Klasifiko rastin ligjor më poshtë. Kthe VETËM JSON:\n"
        '{"category": "civil|criminal|family|commercial|labor|administrative|other", '
        '"city": "qyteti nëse përmendet, ndryshe null", '
        '"urgency": "normal|urgent"}\n\nRASTI:\n' + description[:4000]
    )
    try:
        provider = get_provider(None)
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


async def _free_slot_lines(db: AsyncSession, limit_lawyers: int = 3) -> list[str]:
    """Up to 3 bookable lawyers with their next free slot — the booking
    offer that closes the intake loop."""
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
                locale="sq",
                country="XK",
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
        )
        db.add(case)
        await db.commit()

        slot_lines = await _free_slot_lines(db)

    # Alert the supply side exactly like a web-posted case
    try:
        await _notify_matching_lawyers(case.id, case.category, case.city, case.country)
    except Exception as exc:
        logger.warning("WA intake lawyer alert failed: %s", exc)

    reply = (
        "✅ Rasti u dërgua te avokatët e verifikuar!\n\n"
        f"Ndiqe dhe lexo përgjigjet te: {settings.public_base_url}/rasti-im\n"
        f"(hyr me email-in {email} — përdor 'Harrova fjalëkalimin' herën e parë)"
    )
    if slot_lines:
        reply += (
            "\n\n📅 Termine të lira për konsultë:\n"
            + "\n".join(slot_lines)
            + f"\nRezervo te: {settings.public_base_url}/avokatet"
        )
    return reply


async def handle_intake_message(phone: str, text: str) -> str | None:
    """Advance the intake state machine. Returns the reply to send, or
    None when the message is not part of an intake (normal Q&A applies)."""
    r = aioredis.from_url(settings.redis_url)
    try:
        lowered = text.strip().lower()
        state = await _get_state(r, phone)

        if lowered in _CANCEL_WORDS:
            if state:
                await _set_state(r, phone, None)
                return MSG["cancelled"]
            return None

        if state is None:
            if lowered in _START_WORDS:
                await _set_state(r, phone, {"step": "describe"})
                return MSG["start"]
            return None

        step = state.get("step")
        if step == "describe":
            if len(text.strip()) < MIN_DESCRIPTION:
                return MSG["too_short"]
            state["description"] = text.strip()
            state.update(await _classify(text))
            if state.get("city"):
                state["step"] = "name"
                await _set_state(r, phone, state)
                return MSG["ask_name"]
            state["step"] = "city"
            await _set_state(r, phone, state)
            return MSG["ask_city"]

        if step == "city":
            state["city"] = text.strip()[:120]
            state["step"] = "name"
            await _set_state(r, phone, state)
            return MSG["ask_name"]

        if step == "name":
            state["name"] = text.strip()[:200]
            state["step"] = "email"
            await _set_state(r, phone, state)
            return MSG["ask_email"]

        if step == "email":
            candidate = text.strip()
            if not _EMAIL_RE.match(candidate):
                return MSG["bad_email"]
            state["email"] = candidate
            await _set_state(r, phone, None)
            try:
                return await _finish_intake(phone, state)
            except Exception as exc:
                logger.exception("WA intake finish failed: %s", exc)
                return (
                    "Diçka shkoi keq gjatë postimit — provo përsëri më vonë ose "
                    f"posto direkt te {settings.public_base_url}/posto-rastin"
                )

        # Unknown step — reset defensively
        await _set_state(r, phone, None)
        return None
    finally:
        await r.aclose()


async def daily_hint(r_url: str, phone: str) -> str:
    """The RAST hint, appended at most once per day per phone."""
    try:
        r = aioredis.from_url(r_url)
        first = await r.set(f"wa:hint:{phone}", "1", nx=True, ex=24 * 3600)
        await r.aclose()
        return MSG["hint"] if first else ""
    except Exception:
        return ""
