"""Email notifications: deadline reminders sent per each deadline's
remind_days_before offsets. Redis SETNX guards against duplicate sends.
Disabled entirely when SMTP is not configured in backend/.env."""
import asyncio
import logging
import re
import smtplib
from datetime import UTC, date, datetime, timedelta
from email.message import EmailMessage

import redis.asyncio as aioredis
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.i18n import pick_locale, tr
from app.models import Contact, Deadline, Matter, Tenant, User
from app.services.consent import has_consent
from app.services.push import push_enabled, send_push_to_user
from app.services.sms import send_sms, sms_enabled

logger = logging.getLogger(__name__)

DEDUP_TTL_SECONDS = 3 * 24 * 3600


def smtp_enabled() -> bool:
    return bool(settings.smtp_host)


# Addresses used by the test simulation and demo seeds. Mailing them makes
# Gmail return "Address not found" bounces to the owner's inbox and hurts
# the sender reputation of the whole platform, so they are never sent.
_TEST_RECIPIENT_RE = re.compile(
    # Simulation suffixes are uuid hex (letters+digits), e.g. driton.sim.c9fcc8
    r"(\.sim\.[0-9a-f]+@gmail\.com$"
    # Non-".sim." throwaway identities used by full_simulation.py
    r"|^kontakt\.ferro\.[0-9a-f]+@gmail\.com$"
    r"|^skrap\.[0-9a-f]+@gmail\.com$"
    # isolation_check.py tenants (IsoTest A/B) — self-deleting security probes
    r"|^iso\.[ab]\.[0-9a-f]+@gmail\.com$"
    r"|@example\.(com|org|net)$"
    r"|@avokatim\.(local|app)$"
    r"|@gmail\.con$)",  # common .com typo — the domain does not exist
    re.IGNORECASE,
)


def _is_test_recipient(to: str) -> bool:
    return bool(_TEST_RECIPIENT_RE.search(to.strip()))


def _send_email_sync(
    to: str,
    subject: str,
    body: str,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> None:
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    for filename, content, mime in attachments or []:
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(
            content, maintype=maintype, subtype=subtype or "octet-stream", filename=filename
        )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        if settings.smtp_starttls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


async def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> bool:
    if not smtp_enabled():
        return False
    if _is_test_recipient(to):
        logger.info("Suppressed email to test address %s (%s)", to, subject)
        return True
    try:
        await asyncio.to_thread(_send_email_sync, to, subject, body, attachments)
        return True
    except Exception as exc:
        logger.warning("Email to %s failed: %s", to, exc)
        return False


async def _check_deadline_reminders(redis: aioredis.Redis) -> None:
    now = datetime.now(UTC)
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(
                    Deadline,
                    Matter.reference,
                    Matter.title,
                    Matter.responsible_user_id,
                    Matter.client_id,
                )
                .join(Matter, Matter.id == Deadline.matter_id)
                .where(Deadline.status == "pending", Deadline.due_at >= now)
            )
        ).all()

        for deadline, ref, title, responsible_id, client_id in rows:
            days_left = (deadline.due_at - now).days
            offsets = deadline.remind_days_before or []
            if days_left not in offsets:
                continue
            key = f"reminder:{deadline.id}:{days_left}"
            if not await redis.set(key, "1", nx=True, ex=DEDUP_TTL_SECONDS):
                continue  # already sent
            user = await db.get(User, responsible_id)
            if user is None:
                continue
            loc = pick_locale(user.locale)
            subject = tr(loc, "reminder_subject", days=days_left, title=deadline.title)
            body = (
                f"{tr(loc, 'reminder_matter')}: {ref} — {title}\n"
                f"{tr(loc, 'reminder_deadline')}: {deadline.title}\n"
                f"{tr(loc, 'reminder_expires')}: {deadline.due_at:%d.%m.%Y %H:%M}\n"
                + (
                    f"{tr(loc, 'reminder_legal_basis')}: {deadline.legal_basis}\n"
                    if deadline.legal_basis
                    else ""
                )
                + f"\n{settings.public_base_url}/matters/{deadline.matter_id}\n"
            )
            if user.email:
                await send_email(user.email, subject, body)
            await send_push_to_user(
                db,
                user.id,
                title=subject,
                body=f"{ref} — {deadline.title} · {deadline.due_at:%d.%m.%Y}",
                url=f"/matters/{deadline.matter_id}",
            )
            from app.services.notification_center import notify as notify_center

            await notify_center(
                db, tenant_id=deadline.tenant_id, kind="deadline", title=subject,
                body=f"{ref} — {deadline.title} · {deadline.due_at:%d.%m.%Y}",
                url=f"/matters/{deadline.matter_id}", user_id=user.id, push=False,
            )
            await db.commit()
            # Hearings: also SMS the client, so they show up in court
            if deadline.kind == "hearing" and sms_enabled() and client_id is not None:
                sms_key = f"reminder-sms:{deadline.id}:{days_left}"
                if await redis.set(sms_key, "1", nx=True, ex=DEDUP_TTL_SECONDS):
                    client = await db.get(Contact, client_id)
                    # SMS only with recorded consent (Law 06/L-082 art. 7)
                    if (
                        client is not None
                        and client.phone
                        and await has_consent(db, client.id, "sms")
                    ):
                        tenant = await db.get(Tenant, client.tenant_id)
                        client_loc = pick_locale(
                            client.locale, tenant.default_locale if tenant else None
                        )
                        await send_sms(
                            client.phone,
                            tr(
                                client_loc,
                                "sms_hearing_reminder",
                                title=deadline.title,
                                when=f"{deadline.due_at:%d.%m.%Y %H:%M}",
                                ref=ref,
                            ),
                        )
            logger.info("Reminder sent for deadline %s (%s days)", deadline.id, days_left)


async def _check_onboarding_nudges() -> None:
    """One-shot onboarding reminders (the gap seen with the first real signups):
    - lawyer signed up >1h ago and public profile still not visible -> 1 email
    - citizen signed up >1h ago and email still unverified -> 1 email
    Owner's call: help while the signup is still fresh in the person's mind,
    not two days later. Only accounts from the last 14 days, so old/test
    accounts are never mailed.
    """
    from app.models import CitizenUser, LawyerProfile

    now = datetime.now(UTC)
    window_start = now - timedelta(days=14)

    async with SessionLocal() as db:
        # Lawyers without an active public profile, 1h after signup
        visible_user_ids = select(LawyerProfile.user_id).where(
            LawyerProfile.is_visible.is_(True)
        )
        lawyers = (
            await db.execute(
                select(User).where(
                    User.is_active.is_(True),
                    User.is_superadmin.is_(False),
                    User.profile_nudge_sent_at.is_(None),
                    User.created_at <= now - timedelta(hours=1),
                    User.created_at >= window_start,
                    User.id.not_in(visible_user_ids),
                )
            )
        ).scalars().all()
        for user in lawyers:
            loc = pick_locale(user.locale)
            sent = await send_email(
                user.email,
                tr(loc, "lawyer_profile_nudge_subject"),
                tr(
                    loc,
                    "lawyer_profile_nudge_body",
                    url=f"{settings.public_base_url}/onboarding",
                ),
            )
            user.profile_nudge_sent_at = now
            if sent:
                logger.info("Profile nudge sent to lawyer %s", user.email)

        # Citizens with unverified email, 1h after signup
        from app.security import create_purpose_token

        citizens = (
            await db.execute(
                select(CitizenUser).where(
                    CitizenUser.is_active.is_(True),
                    CitizenUser.email_verified_at.is_(None),
                    CitizenUser.verify_reminder_sent_at.is_(None),
                    CitizenUser.created_at <= now - timedelta(hours=1),
                    CitizenUser.created_at >= window_start,
                )
            )
        ).scalars().all()
        for citizen in citizens:
            loc = pick_locale(citizen.locale)
            token = create_purpose_token("citizen_verify", citizen.id, minutes=60 * 24 * 3)
            url = f"{settings.public_base_url}/rasti-im?verifiko={token}"
            sent = await send_email(
                citizen.email,
                tr(loc, "citizen_verify_reminder_subject"),
                tr(loc, "citizen_verify_reminder_body", url=url),
            )
            citizen.verify_reminder_sent_at = now
            if sent:
                logger.info("Verify reminder sent to citizen %s", citizen.email)

        # Activation follow-up: verified citizens who never posted a case,
        # once, 48h after signup (Clio 2026: intake follow-up is the single
        # highest-ROI automation — people who registered clearly had a need)
        from app.models import CaseRequest

        posters = select(CaseRequest.citizen_id)
        idle_citizens = (
            await db.execute(
                select(CitizenUser).where(
                    CitizenUser.is_active.is_(True),
                    CitizenUser.email_verified_at.is_not(None),
                    CitizenUser.case_followup_sent_at.is_(None),
                    CitizenUser.created_at <= now - timedelta(hours=48),
                    CitizenUser.created_at >= window_start,
                    CitizenUser.id.not_in(posters),
                )
            )
        ).scalars().all()
        for citizen in idle_citizens:
            loc = pick_locale(citizen.locale)
            sent = await send_email(
                citizen.email,
                tr(loc, "citizen_case_followup_subject"),
                tr(
                    loc,
                    "citizen_case_followup_body",
                    post_url=f"{settings.public_base_url}/posto-rastin",
                    ava_url=f"{settings.public_base_url}/ava",
                ),
            )
            citizen.case_followup_sent_at = now
            if sent:
                logger.info("Case follow-up sent to citizen %s", citizen.email)

        await db.commit()


async def _check_review_requests() -> None:
    """One-shot review invitation: a claimed case that concluded (converted or
    closed) 48h+ ago, has no review yet and no invitation sent, gets a single
    email pointing to /rasti-im where the rating form lives."""
    from app.models import CaseRequest, CaseReview, CitizenUser

    now = datetime.now(UTC)
    async with SessionLocal() as db:
        reviewed = select(CaseReview.case_request_id)
        cases = (
            (
                await db.execute(
                    select(CaseRequest).where(
                        CaseRequest.claimed_by_tenant_id.is_not(None),
                        CaseRequest.status.in_(["converted", "closed"]),
                        CaseRequest.review_request_sent_at.is_(None),
                        # updated_at is when the status flipped to concluded
                        CaseRequest.updated_at <= now - timedelta(hours=48),
                        CaseRequest.id.not_in(reviewed),
                    )
                )
            )
            .scalars()
            .all()
        )
        for case in cases:
            citizen = await db.get(CitizenUser, case.citizen_id)
            if citizen is None or not citizen.is_active or citizen.email_verified_at is None:
                case.review_request_sent_at = now  # never retry dead ends
                continue
            loc = pick_locale(case.locale or citizen.locale)
            sent = await send_email(
                citizen.email,
                tr(loc, "case_review_request_subject"),
                tr(
                    loc,
                    "case_review_request_body",
                    url=f"{settings.public_base_url}/rasti-im",
                ),
            )
            case.review_request_sent_at = now
            if sent:
                logger.info("Review request sent for case %s", case.id)
        await db.commit()


async def _generate_time_suggestions_nightly() -> None:
    """Run passive time capture once per day per tenant (idempotent — the
    generator skips windows that already have a suggestion)."""
    from app.services.time_capture import generate_suggestions

    async with SessionLocal() as db:
        tenant_ids = (
            (await db.execute(select(Tenant.id).where(Tenant.status == "active")))
            .scalars()
            .all()
        )
        for tenant_id in tenant_ids:
            created = await generate_suggestions(db, tenant_id)
            if created:
                await db.commit()


async def reminder_loop() -> None:
    """Background task started from the app lifespan. Runs even without
    SMTP/push/SMS since D-054: the in-app notification center is always a
    delivery channel."""
    if not smtp_enabled() and not push_enabled() and not sms_enabled():
        logger.info("No SMTP/Web Push/SMS — reminders go to the in-app center only")
    redis = aioredis.from_url(settings.redis_url)
    logger.info("Deadline reminder loop started (every %s min)", settings.reminder_check_minutes)
    last_time_capture_day: str | None = None
    last_proactive_day: str | None = None
    while True:
        try:
            await _check_deadline_reminders(redis)
        except Exception as exc:
            logger.warning("Reminder check failed: %s", exc)
        if smtp_enabled():
            try:
                await _check_onboarding_nudges()
            except Exception as exc:
                logger.warning("Onboarding nudge check failed: %s", exc)
            try:
                await _check_review_requests()
            except Exception as exc:
                logger.warning("Review request check failed: %s", exc)
        today = date.today().isoformat()
        if today != last_time_capture_day:
            try:
                await _generate_time_suggestions_nightly()
                last_time_capture_day = today
            except Exception as exc:
                logger.warning("Time-capture generation failed: %s", exc)

        # Proactive AI (D-054 F3). Briefings check every iteration (they are
        # hour-gated + redis-deduped); the heavier monitors once per day.
        from app.services import proactive

        try:
            await proactive.run_morning_briefings(redis)
        except Exception as exc:
            logger.warning("Morning briefing run failed: %s", exc)
        if today != last_proactive_day:
            try:
                await proactive.run_caselaw_monitor(redis)
                await proactive.run_deadline_audit(redis)
                last_proactive_day = today
            except Exception as exc:
                logger.warning("Proactive monitors failed: %s", exc)
        await asyncio.sleep(settings.reminder_check_minutes * 60)
