"""Consultation booking (Phase 4): a citizen reserves a slot with a
directory lawyer; the lawyer confirms or declines.

Availability is a weekly recurring schedule on the lawyer's profile
([{"day": 0, "start": "09:00", "end": "12:00"}], day 0 = Monday). Free
slots for the next 14 days are the schedule windows split into 30-minute
steps minus existing pending/confirmed bookings.
"""
import logging
import re
import uuid
from datetime import UTC, datetime, time, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.marketplace import _current_citizen, _ip, _rate_limit
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.i18n import pick_locale, tr
from app.models import CitizenUser, ConsultBooking, LawyerProfile, Tenant, User
from app.services.audit import log_action
from app.services.notifications import _is_test_recipient, send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["bookings"])
public_router = APIRouter(prefix="/public", tags=["public"])

SLOT_MINUTES = 30
HORIZON_DAYS = 14
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _parse_hhmm(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def _free_slots(profile: LawyerProfile, taken: set[datetime]) -> list[datetime]:
    """Concrete bookable start times for the next HORIZON_DAYS days,
    in the server's local timezone."""
    tz = datetime.now(UTC).astimezone().tzinfo
    now = datetime.now(tz)
    slots: list[datetime] = []
    for offset in range(HORIZON_DAYS):
        day = (now + timedelta(days=offset)).date()
        for window in profile.booking_slots or []:
            if window.get("day") != day.weekday():
                continue
            cursor = datetime.combine(day, _parse_hhmm(window["start"]), tzinfo=tz)
            end = datetime.combine(day, _parse_hhmm(window["end"]), tzinfo=tz)
            while cursor + timedelta(minutes=SLOT_MINUTES) <= end:
                if cursor > now and cursor not in taken:
                    slots.append(cursor)
                cursor += timedelta(minutes=SLOT_MINUTES)
    return sorted(slots)


async def _taken_starts(db: AsyncSession, tenant_id: uuid.UUID) -> set[datetime]:
    tz = datetime.now(UTC).astimezone().tzinfo
    rows = await db.execute(
        select(ConsultBooking.starts_at).where(
            ConsultBooking.tenant_id == tenant_id,
            ConsultBooking.status.in_(["pending_payment", "pending", "confirmed"]),
            ConsultBooking.starts_at >= datetime.now(UTC),
        )
    )
    return {row[0].astimezone(tz) for row in rows}


def _booking_out(booking: ConsultBooking, other_party: str | None = None) -> dict:
    return {
        "id": str(booking.id),
        "starts_at": booking.starts_at.isoformat(),
        "duration_min": booking.duration_min,
        "status": booking.status,
        "note": booking.note,
        "with": other_party,
        "fee_eur": booking.fee_eur,
        "attachment_name": booking.attachment_name,
        "created_at": booking.created_at.isoformat(),
    }


# ---------- lawyer side ----------

class BookingSettingsIn(BaseModel):
    enabled: bool
    slots: list[dict] = Field(default_factory=list, max_length=21)


@router.get("/booking-settings")
async def get_booking_settings(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    profile = (
        await db.execute(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    ).scalar_one_or_none()
    return {
        "enabled": bool(profile and profile.booking_enabled),
        "slots": (profile.booking_slots if profile else []) or [],
        "has_profile": profile is not None,
    }


@router.put("/booking-settings")
async def update_booking_settings(
    body: BookingSettingsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = (
        await db.execute(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    ).scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Create your public profile first"
        )
    for window in body.slots:
        day = window.get("day")
        start_s, end_s = window.get("start", ""), window.get("end", "")
        if (
            not isinstance(day, int)
            or not 0 <= day <= 6
            or not _TIME_RE.match(start_s)
            or not _TIME_RE.match(end_s)
            or _parse_hhmm(start_s) >= _parse_hhmm(end_s)
        ):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid slot window")
    profile.booking_enabled = body.enabled
    profile.booking_slots = [
        {"day": w["day"], "start": w["start"], "end": w["end"]} for w in body.slots
    ]
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="booking.settings",
        entity_type="lawyer_profile", entity_id=str(profile.id),
        details={"enabled": body.enabled, "windows": len(body.slots)},
    )
    await db.commit()
    return {"enabled": profile.booking_enabled, "slots": profile.booking_slots}


@router.get("/bookings")
async def lawyer_bookings(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(ConsultBooking, CitizenUser)
            .join(CitizenUser, CitizenUser.id == ConsultBooking.citizen_id)
            .where(
                ConsultBooking.tenant_id == user.tenant_id,
                ConsultBooking.starts_at >= datetime.now(UTC) - timedelta(days=1),
            )
            .order_by(ConsultBooking.starts_at)
        )
    ).all()
    return [
        {**_booking_out(b, citizen.full_name), "citizen_email": citizen.email}
        for b, citizen in rows
    ]


@router.get("/bookings/{booking_id}/attachment")
async def booking_attachment(
    booking_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The prepared dossier the citizen attached when booking (PDF draft
    from /dokumentet) — the professional reviews it before the meeting."""
    import base64

    from fastapi.responses import Response

    booking = await db.get(ConsultBooking, booking_id)
    if booking is None or booking.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if not booking.attachment_b64:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No attachment")
    try:
        content = base64.b64decode(booking.attachment_b64)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Corrupt attachment")
    name = booking.attachment_name or "dosja.pdf"
    return Response(
        content,
        media_type="application/pdf" if name.lower().endswith(".pdf") else "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


class DecideIn(BaseModel):
    action: str  # confirm | decline


async def _notify_citizen_decision(booking_id: uuid.UUID, confirmed: bool) -> None:
    """Own session: runs as background task after commit."""
    from app.database import SessionLocal

    async with SessionLocal() as db:
        booking = await db.get(ConsultBooking, booking_id)
        if booking is None:
            return
        citizen = await db.get(CitizenUser, booking.citizen_id)
        lawyer = (
            await db.get(User, booking.lawyer_user_id) if booking.lawyer_user_id else None
        )
        tenant = await db.get(Tenant, booking.tenant_id)
        if citizen is None:
            return
        loc = pick_locale(citizen.locale)
        when = booking.starts_at.astimezone().strftime("%d.%m.%Y %H:%M")
        lawyer_name = (lawyer.full_name if lawyer else None) or (
            tenant.name if tenant else "AvokatIM"
        )
        key = "booking_confirmed" if confirmed else "booking_declined"
        await send_email(
            citizen.email,
            tr(loc, f"{key}_subject"),
            tr(loc, f"{key}_body", lawyer=lawyer_name, when=when,
               url=f"{settings.public_base_url}/avokatet"),
        )


@router.post("/bookings/{booking_id}/decide")
async def lawyer_decide_booking(
    booking_id: uuid.UUID,
    body: DecideIn,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.action not in ("confirm", "decline"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid action")
    booking = await db.get(ConsultBooking, booking_id)
    if booking is None or booking.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already decided")
    booking.status = "confirmed" if body.action == "confirm" else "declined"
    booking.lawyer_user_id = booking.lawyer_user_id or user.id
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action=f"booking.{body.action}",
        entity_type="consult_booking", entity_id=str(booking.id),
    )
    await db.commit()
    background.add_task(
        _notify_citizen_decision, booking.id, booking.status == "confirmed"
    )
    return _booking_out(booking)


# ---------- public / citizen side ----------

async def _bookable_profile(
    db: AsyncSession, profile_id: uuid.UUID
) -> tuple[LawyerProfile, User]:
    row = (
        await db.execute(
            select(LawyerProfile, User)
            .join(User, User.id == LawyerProfile.user_id)
            .join(Tenant, Tenant.id == LawyerProfile.tenant_id)
            .where(
                LawyerProfile.id == profile_id,
                LawyerProfile.is_visible.is_(True),
                LawyerProfile.verification_status == "verified",
                LawyerProfile.booking_enabled.is_(True),
                User.is_active.is_(True),
                Tenant.status == "active",
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lawyer not found")
    return row


@public_router.get("/lawyers/{profile_id}/slots")
async def public_lawyer_slots(profile_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    profile, _ = await _bookable_profile(db, profile_id)
    taken = await _taken_starts(db, profile.tenant_id)
    return {
        "slot_minutes": SLOT_MINUTES,
        "slots": [s.isoformat() for s in _free_slots(profile, taken)],
    }


class BookIn(BaseModel):
    profile_id: uuid.UUID
    starts_at: datetime
    note: str | None = Field(default=None, max_length=1000)
    # Prepared dossier (notary flow): draft PDF generated at /dokumentet,
    # base64-encoded; ~2 MB file limit keeps rows small
    attachment_name: str | None = Field(default=None, max_length=200)
    attachment_b64: str | None = Field(default=None, max_length=3_000_000)


async def _notify_lawyer_new_booking(booking_id: uuid.UUID) -> None:
    """Own session: runs as background task after commit."""
    from app.database import SessionLocal
    from app.services.push import send_push_to_user

    async with SessionLocal() as db:
        booking = await db.get(ConsultBooking, booking_id)
        if booking is None or booking.lawyer_user_id is None:
            return
        lawyer = await db.get(User, booking.lawyer_user_id)
        citizen = await db.get(CitizenUser, booking.citizen_id)
        if lawyer is None or citizen is None:
            return
        loc = pick_locale(lawyer.locale)
        when = booking.starts_at.astimezone().strftime("%d.%m.%Y %H:%M")
        subject = tr(loc, "booking_new_subject")
        body = tr(loc, "booking_new_body", citizen=citizen.full_name, when=when,
                  url=f"{settings.public_base_url}/marketplace")
        await send_push_to_user(db, lawyer.id, title=subject, body=body, url="/marketplace")
        await send_email(lawyer.email, subject, body)


@public_router.post("/citizen/bookings", status_code=201)
async def citizen_create_booking(
    body: BookIn,
    request: Request,
    background: BackgroundTasks,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    await _rate_limit("citizen_booking", str(citizen.id), limit=5, window_seconds=24 * 3600)
    profile, lawyer = await _bookable_profile(db, body.profile_id)
    taken = await _taken_starts(db, profile.tenant_id)
    starts_local = body.starts_at.astimezone(datetime.now(UTC).astimezone().tzinfo)
    if starts_local not in set(_free_slots(profile, taken)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot no longer available")
    # Online consultation payment: when the lawyer set a fee and Stripe is
    # configured, the booking waits for checkout to complete (webhook flips
    # it to pending and only then notifies the lawyer). Without Stripe the
    # fee is transparent info only and the flow is unchanged.
    from app.services.payments import create_payment_link, payments_enabled

    charge_online = bool(profile.consult_fee_eur) and payments_enabled()
    booking = ConsultBooking(
        citizen_id=citizen.id,
        tenant_id=profile.tenant_id,
        lawyer_user_id=lawyer.id,
        starts_at=starts_local,
        duration_min=SLOT_MINUTES,
        note=body.note,
        status="pending_payment" if charge_online else "pending",
        fee_eur=profile.consult_fee_eur if charge_online else None,
        attachment_name=body.attachment_name if body.attachment_b64 else None,
        attachment_b64=body.attachment_b64,
    )
    db.add(booking)
    await db.flush()

    checkout_url: str | None = None
    if charge_online:
        try:
            checkout_url, _session_id = await create_payment_link(
                invoice_id=str(booking.id),
                invoice_number=f"KONSULTA-{str(booking.id)[:8]}",
                amount_cents=int(profile.consult_fee_eur) * 100,
                currency="eur",
                description=f"Konsultë ligjore — {lawyer.full_name}",
                customer_email=citizen.email,
                metadata_key="booking_id",
                return_path="/rasti-im",
            )
        except RuntimeError as exc:
            logger.warning("Stripe checkout for booking failed: %s", exc)
            # Fail-open: don't lose the booking because the gateway hiccuped
            booking.status = "pending"
            booking.fee_eur = None
            charge_online = False

    await log_action(
        db, tenant_id=profile.tenant_id, user_id=None, action="booking.create",
        entity_type="consult_booking", entity_id=str(booking.id),
        details={"starts_at": starts_local.isoformat(),
                 "paid_online": charge_online}, ip_address=_ip(request),
    )
    await db.commit()
    if not charge_online:
        background.add_task(_notify_lawyer_new_booking, booking.id)
    if not _is_test_recipient(citizen.email):
        from app.services.ops_notify import notify_ops

        background.add_task(
            notify_ops, "rezervim",
            f"Rezervim i ri konsulte te {lawyer.full_name} "
            f"({starts_local:%d.%m.%Y %H:%M})"
            + (f", pagesë online {profile.consult_fee_eur} EUR" if charge_online else "")
            + ".",
        )
    return {**_booking_out(booking, lawyer.full_name), "checkout_url": checkout_url}


@public_router.get("/citizen/bookings")
async def citizen_my_bookings(
    citizen: CitizenUser = Depends(_current_citizen), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(ConsultBooking, User.full_name)
            .outerjoin(User, User.id == ConsultBooking.lawyer_user_id)
            .where(ConsultBooking.citizen_id == citizen.id)
            .order_by(ConsultBooking.starts_at.desc())
        )
    ).all()
    return [_booking_out(b, name) for b, name in rows]


@public_router.post("/citizen/bookings/{booking_id}/cancel")
async def citizen_cancel_booking(
    booking_id: uuid.UUID,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    booking = await db.get(ConsultBooking, booking_id)
    if booking is None or booking.citizen_id != citizen.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.status not in ("pending_payment", "pending", "confirmed"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot cancel")
    booking.status = "cancelled"
    await log_action(
        db, tenant_id=booking.tenant_id, user_id=None, action="booking.cancel",
        entity_type="consult_booking", entity_id=str(booking.id),
    )
    await db.commit()
    return _booking_out(booking)
