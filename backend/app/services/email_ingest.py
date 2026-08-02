"""Email-to-matter ingestion: an IMAP poller that files incoming mail into
the matter whose alias it was sent to.

Every matter can get a unique inbound address using plus addressing:
    <imap_user local part>+<matter email_token>@<domain>
The lawyer CCs (or forwards mail to) that address; the poller stores the
email body as a matter note and every attachment as a matter document.
Disabled entirely when IMAP is not configured in backend/.env."""
import asyncio
import email
import email.policy
import imaplib
import logging
import re
import secrets
import uuid
from email.utils import parseaddr

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.models import Contact, Document, EmailSuggestion, Matter, MatterNote
from app.services import deadline_suggest, storage
from app.services.audit import log_action

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"\+([a-z0-9]{10,32})@", re.IGNORECASE)
_DEDUP_TTL = 30 * 24 * 3600


def imap_enabled() -> bool:
    return bool(settings.imap_host and settings.imap_user)


def matter_inbound_address(token: str) -> str:
    """Build the matter's alias from the configured mailbox user."""
    local, _, domain = settings.imap_user.partition("@")
    return f"{local}+{token}@{domain}"


async def ensure_email_token(db: AsyncSession, matter: Matter) -> str:
    if not matter.email_token:
        matter.email_token = secrets.token_hex(8)  # 16 lowercase hex chars
        await db.commit()
    return matter.email_token


def _fetch_unseen_sync() -> list[tuple[bytes, bytes]]:
    """Fetch unseen messages; returns [(uid, raw_message)]. Marks them seen."""
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as imap:
        imap.login(settings.imap_user, settings.imap_password)
        imap.select(settings.imap_folder)
        _, data = imap.uid("search", None, "UNSEEN")
        uids = data[0].split() if data and data[0] else []
        messages = []
        for uid in uids[:50]:  # safety cap per poll
            _, msg_data = imap.uid("fetch", uid, "(RFC822)")
            if msg_data and msg_data[0]:
                messages.append((uid, msg_data[0][1]))
                imap.uid("store", uid, "+FLAGS", "(\\Seen)")
        return messages


def _extract_token(msg: email.message.EmailMessage) -> str | None:
    for header in ("to", "cc", "bcc", "delivered-to", "x-original-to", "envelope-to"):
        for value in msg.get_all(header, []):
            match = _TOKEN_RE.search(value)
            if match:
                return match.group(1).lower()
    return None


def _body_text(msg: email.message.EmailMessage) -> str:
    body = msg.get_body(preferencelist=("plain", "html"))
    if body is None:
        return ""
    text = body.get_content()
    if body.get_content_type() == "text/html":
        text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


async def _file_message(db: AsyncSession, matter: Matter, msg: email.message.EmailMessage) -> None:
    sender = msg.get("from", "?")
    subject = msg.get("subject", "(pa subjekt)")
    body = _body_text(msg)

    note = MatterNote(
        tenant_id=matter.tenant_id,
        matter_id=matter.id,
        author_id=matter.responsible_user_id,
        body=f"📧 Email nga {sender}\nSubjekti: {subject}\n\n{body[:20000]}",
    )
    db.add(note)

    saved = 0
    scan_docs: list[Document] = []
    for part in msg.iter_attachments():
        filename = part.get_filename()
        content = part.get_payload(decode=True)
        if not filename or not content:
            continue
        rel_path, sha, encrypted = storage.save_file(content, matter.tenant_id)
        mime = part.get_content_type() or "application/octet-stream"
        text, ocr_status = storage.extract_text(content, mime, filename)
        doc = Document(
            tenant_id=matter.tenant_id,
            matter_id=matter.id,
            family_id=uuid.uuid4(),
            version=1,
            is_latest=True,
            filename=filename,
            mime_type=mime,
            size_bytes=len(content),
            sha256=sha,
            storage_path=rel_path,
            encrypted=encrypted,
            category="email",
            uploaded_by_id=matter.responsible_user_id,
            text_content=text or None,
            ocr_status=ocr_status,
        )
        db.add(doc)
        scan_docs.append(doc)
        saved += 1

    await log_action(
        db, tenant_id=matter.tenant_id, user_id=None, action="email.ingested",
        entity_type="matter", entity_id=str(matter.id),
        details={"from": sender, "subject": subject, "attachments": saved},
    )
    await db.commit()
    # D-043: propose deadlines from attachments that carry text (background,
    # suggest→accept — nothing auto-created).
    for doc in scan_docs:
        if doc.text_content:
            deadline_suggest.scan_document_background(doc.id, source="email")
    logger.info(
        "Email filed into matter %s (%s attachment(s))", matter.reference, saved
    )


# ---------- Token-less classification (D-043): sender ↔ contact match ----------


def _sender_address(msg: email.message.EmailMessage) -> str:
    return (parseaddr(msg.get("from", ""))[1] or "").strip().lower()


def _best_matter(matters: list[Matter]) -> Matter | None:
    """Prefer open matters; among equals, the most recently updated one."""
    if not matters:
        return None
    return min(
        matters,
        key=lambda m: (
            m.status != "open",
            -(m.updated_at.timestamp() if m.updated_at else 0),
        ),
    )


async def _suggest_from_sender(
    db: AsyncSession, msg: email.message.EmailMessage, raw: bytes
) -> bool:
    """Inbound mail without a matter token: if the sender is a known contact
    with a matter, park the message as an EmailSuggestion. Nothing is filed
    until the lawyer accepts (suggest → accept, D-043)."""
    sender = _sender_address(msg)
    if not sender:
        return False
    contacts = (
        await db.execute(select(Contact).where(func.lower(Contact.email) == sender))
    ).scalars().all()
    for contact in contacts:
        matters = (
            await db.execute(
                select(Matter).where(
                    Matter.tenant_id == contact.tenant_id,
                    Matter.client_id == contact.id,
                )
            )
        ).scalars().all()
        matter = _best_matter(matters)
        if matter is None:
            continue
        rel_path, _sha, encrypted = storage.save_file(raw, contact.tenant_id)
        db.add(
            EmailSuggestion(
                tenant_id=contact.tenant_id,
                matter_id=matter.id,
                contact_id=contact.id,
                sender=sender,
                subject=(msg.get("subject") or "")[:500],
                body_preview=_body_text(msg)[:2000],
                raw_path=rel_path,
                raw_encrypted=encrypted,
            )
        )
        from app.services.notification_center import notify as notify_center

        await notify_center(
            db, tenant_id=contact.tenant_id, kind="email",
            title=f"✉ {contact.display_name}: {(msg.get('subject') or '')[:120]}",
            body=_body_text(msg)[:200], url="/dashboard",
        )
        await db.commit()
        logger.info(
            "Inbound email from %s parked as suggestion for matter %s",
            sender, matter.reference,
        )
        return True
    return False


async def file_suggested_message(db: AsyncSession, suggestion: EmailSuggestion) -> None:
    """Accept path: parse the stored raw message and file it into the matter
    (note + attachments + deadline scan) exactly like a token-addressed email."""
    matter = await db.get(Matter, suggestion.matter_id)
    raw = storage.load_file(suggestion.raw_path, suggestion.raw_encrypted)
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    await _file_message(db, matter, msg)


async def _poll_once(redis: aioredis.Redis) -> None:
    messages = await asyncio.to_thread(_fetch_unseen_sync)
    if not messages:
        return
    async with SessionLocal() as db:
        for _uid, raw in messages:
            msg = email.message_from_bytes(raw, policy=email.policy.default)
            message_id = msg.get("message-id", "").strip()
            if message_id:
                if not await redis.set(f"email-in:{message_id}", "1", nx=True, ex=_DEDUP_TTL):
                    continue  # already processed
            token = _extract_token(msg)
            if token is None:
                if not await _suggest_from_sender(db, msg, raw):
                    logger.info("Inbound email without matter token — skipped")
                continue
            matter = (
                await db.execute(select(Matter).where(Matter.email_token == token))
            ).scalar_one_or_none()
            if matter is None:
                logger.warning("Inbound email with unknown matter token %s", token)
                continue
            await _file_message(db, matter, msg)


async def email_ingest_loop() -> None:
    """Background task started from the app lifespan."""
    if not imap_enabled():
        logger.info("IMAP not configured — email-to-matter ingestion disabled")
        return
    redis = aioredis.from_url(settings.redis_url)
    logger.info("Email ingestion loop started (every %s min)", settings.imap_poll_minutes)
    while True:
        try:
            await _poll_once(redis)
        except Exception as exc:
            logger.warning("Email ingestion failed: %s", exc)
        await asyncio.sleep(settings.imap_poll_minutes * 60)
