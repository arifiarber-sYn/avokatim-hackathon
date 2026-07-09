"""Email notifications: deadline reminders sent per each deadline's
remind_days_before offsets. Redis SETNX guards against duplicate sends.
Disabled entirely when SMTP is not configured in backend/.env."""
import asyncio
import logging
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage

import redis.asyncio as aioredis
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.i18n import pick_locale, tr
from app.models import Contact, Deadline, Matter, Tenant, User
from app.services.push import push_enabled, send_push_to_user
from app.services.sms import send_sms, sms_enabled

logger = logging.getLogger(__name__)

DEDUP_TTL_SECONDS = 3 * 24 * 3600


def smtp_enabled() -> bool:
    return bool(settings.smtp_host)


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
            # Hearings: also SMS the client, so they show up in court
            if deadline.kind == "hearing" and sms_enabled() and client_id is not None:
                sms_key = f"reminder-sms:{deadline.id}:{days_left}"
                if await redis.set(sms_key, "1", nx=True, ex=DEDUP_TTL_SECONDS):
                    client = await db.get(Contact, client_id)
                    if client is not None and client.phone:
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


async def reminder_loop() -> None:
    """Background task started from the app lifespan."""
    if not smtp_enabled() and not push_enabled() and not sms_enabled():
        logger.info("Neither SMTP, Web Push nor SMS configured — deadline reminders disabled")
        return
    redis = aioredis.from_url(settings.redis_url)
    logger.info("Deadline reminder loop started (every %s min)", settings.reminder_check_minutes)
    while True:
        try:
            await _check_deadline_reminders(redis)
        except Exception as exc:
            logger.warning("Reminder check failed: %s", exc)
        await asyncio.sleep(settings.reminder_check_minutes * 60)
