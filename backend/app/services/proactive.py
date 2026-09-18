"""Proactive AI layer (D-054 F3): agents that work in the background and
speak up only when it matters (human-on-the-loop, interrupt budget via the
notification prefs from F1).

1. Morning briefing  — daily LLM summary of the tenant's day.
2. Case-law monitor  — new corpus judgments matched to active matters via
                       local embeddings. Nothing leaves the machine.
3. Deadline audit    — active matters with no upcoming deadline.
4. File-quality audit — nightly deterministic hygiene checks on open
                       matters (audit 2026-09-18, the Eve pattern): missing
                       opposing party, no documents, stale draft invoices,
                       matters idle >30 days. No LLM — pure queries.

All of these only create notifications/suggestions; no action is ever taken
without the lawyer (D-044).
"""
import logging
import uuid
from datetime import UTC, date, datetime, timedelta

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.llm import LOCAL_PINNED, get_provider
from app.llm.base import ChatMessage
from app.models import (
    Deadline,
    DeadlineSuggestion,
    Document,
    EmailSuggestion,
    Invoice,
    Jurisdiction,
    LegalCorpusChunk,
    LegalCorpusDoc,
    Matter,
    MatterParty,
    Task,
    Tenant,
)
from app.services.notification_center import notify

logger = logging.getLogger(__name__)

# Only surface judgment matches at least this similar (cosine distance cap)
_CASELAW_MAX_DISTANCE = 0.45
_CASELAW_WINDOW_DAYS = 7
_MATTERS_PER_TENANT = 60

BRIEFING_PROMPT = """Je Ava, asistentja e zyrës ligjore. Shkruaj briefingun e mëngjesit
për avokatin — të shkurtër (max 120 fjalë), të ngrohtë dhe konkret, në gjuhën me kod '{locale}'.
Fillo me përshëndetje një-fjalëshe. Rendit vetëm çka ka rëndësi sot, me numra.
Mos shpik asgjë — përdor VETËM të dhënat më poshtë. Pa formatim markdown.

TË DHËNAT E SOTME:
{data}"""


async def _briefing_data(db: AsyncSession, tenant_id: uuid.UUID) -> tuple[str, dict]:
    """Collects the day's facts. Returns (plain_text, counts)."""
    now = datetime.now(UTC)
    soon = now + timedelta(days=3)

    deadlines = (
        await db.execute(
            select(Deadline, Matter.reference)
            .join(Matter, Matter.id == Deadline.matter_id)
            .where(
                Deadline.tenant_id == tenant_id,
                Deadline.status == "pending",
                Deadline.due_at >= now,
                Deadline.due_at <= soon,
            )
            .order_by(Deadline.due_at)
            .limit(10)
        )
    ).all()

    async def _count(stmt) -> int:
        return (await db.execute(stmt)).scalar_one()

    pending_dl_suggestions = await _count(
        select(func.count(DeadlineSuggestion.id)).where(
            DeadlineSuggestion.tenant_id == tenant_id,
            DeadlineSuggestion.status == "pending",
        )
    )
    pending_emails = await _count(
        select(func.count(EmailSuggestion.id)).where(
            EmailSuggestion.tenant_id == tenant_id,
            EmailSuggestion.status == "pending",
        )
    )
    overdue_invoices = await _count(
        select(func.count(Invoice.id)).where(
            Invoice.tenant_id == tenant_id,
            Invoice.status == "sent",
            Invoice.due_on.is_not(None),
            Invoice.due_on < date.today(),
        )
    )
    open_tasks = await _count(
        select(func.count(Task.id)).where(
            Task.tenant_id == tenant_id,
            Task.status != "done",
            Task.due_date.is_not(None),
            Task.due_date <= date.today(),
        )
    )

    lines = []
    for d, ref in deadlines:
        kind = "SEANCË" if d.kind == "hearing" else "Afat"
        lines.append(f"- {kind}: {d.title} ({ref}) — {d.due_at:%d.%m.%Y %H:%M}")
    if pending_dl_suggestions:
        lines.append(f"- {pending_dl_suggestions} sugjerime afatesh presin aprovim")
    if pending_emails:
        lines.append(f"- {pending_emails} email-e presin klasifikim")
    if overdue_invoices:
        lines.append(f"- {overdue_invoices} fatura të vonuara (Mahnung?)")
    if open_tasks:
        lines.append(f"- {open_tasks} detyra me afat sot ose të kaluara")
    # File-quality audit findings (advancement #7) ride along in the briefing
    try:
        for f in await _file_quality_findings(db, tenant_id):
            lines.append(f"- Higjiena e dosjeve: {f}")
    except Exception:  # never break the briefing over the audit
        logger.exception("file-quality findings failed in briefing")

    if not lines:
        lines.append("- Ditë e qetë: asnjë afat brenda 3 ditëve, asgjë në pritje.")

    counts = {
        "deadlines": len(deadlines),
        "suggestions": pending_dl_suggestions,
        "emails": pending_emails,
        "invoices": overdue_invoices,
        "tasks": open_tasks,
    }
    return "\n".join(lines), counts


async def _generate_briefing(db: AsyncSession, tenant: Tenant) -> str:
    data, _counts = await _briefing_data(db, tenant.id)
    provider_name = None if tenant.allow_external_ai else LOCAL_PINNED
    try:
        provider = get_provider(provider_name)
        result = await provider.chat(
            [
                ChatMessage(
                    role="user",
                    content=BRIEFING_PROMPT.format(
                        locale=tenant.default_locale or "sq", data=data
                    ),
                )
            ]
        )
        text = result.content.strip()
        if text:
            return text[:2000]
    except Exception as exc:
        logger.info("Briefing LLM unavailable (%s) — plain fallback", exc)
    return data


async def run_morning_briefings(redis: aioredis.Redis) -> None:
    """Once per tenant per day, after the configured local hour."""
    if datetime.now().hour < settings.briefing_hour:
        return
    today = date.today().isoformat()
    async with SessionLocal() as db:
        tenants = (
            await db.execute(select(Tenant).where(Tenant.status == "active"))
        ).scalars().all()
        for tenant in tenants:
            key = f"briefing:{tenant.id}:{today}"
            if not await redis.set(key, "1", nx=True, ex=36 * 3600):
                continue
            try:
                text = await _generate_briefing(db, tenant)
                await notify(
                    db, tenant_id=tenant.id, kind="briefing",
                    title=f"☀ Briefingu · {date.today():%d.%m.%Y}",
                    body=text, url="/dashboard",
                )
                await db.commit()
            except Exception as exc:
                logger.warning("Briefing failed for tenant %s: %s", tenant.id, exc)
                await db.rollback()


async def run_caselaw_monitor(redis: aioredis.Redis) -> None:
    """Match judgments recently added to the corpus against active matters
    using local embeddings; notify with the citation when close enough.
    (RA-MICRO ships a static judgment DB — active matching is our edge.)"""
    from app.services.rag import embed

    cutoff = datetime.now(UTC) - timedelta(days=_CASELAW_WINDOW_DAYS)
    async with SessionLocal() as db:
        # Skip everything if no new judgments landed — the common case
        new_docs = (
            await db.execute(
                select(func.count(LegalCorpusDoc.id)).where(
                    LegalCorpusDoc.doc_type == "judgment",
                    LegalCorpusDoc.created_at >= cutoff,
                )
            )
        ).scalar_one()
        if not new_docs:
            return

        matters = (
            await db.execute(
                select(Matter, Tenant)
                .join(Tenant, Tenant.id == Matter.tenant_id)
                .where(Matter.status == "open", Tenant.status == "active")
                .order_by(Matter.updated_at.desc())
                .limit(_MATTERS_PER_TENANT * 5)
            )
        ).all()

        for matter, _tenant in matters:
            query = f"{matter.title}. {matter.description or ''}"[:1000]
            vectors = embed([query])
            if not vectors:
                return  # no local model — nothing to do this round
            row = (
                await db.execute(
                    select(
                        LegalCorpusChunk,
                        LegalCorpusDoc,
                        LegalCorpusChunk.embedding.cosine_distance(vectors[0]).label("dist"),
                    )
                    .join(LegalCorpusDoc, LegalCorpusDoc.id == LegalCorpusChunk.doc_id)
                    .where(
                        LegalCorpusDoc.doc_type == "judgment",
                        LegalCorpusDoc.created_at >= cutoff,
                        LegalCorpusDoc.jurisdiction_id == matter.jurisdiction_id,
                        LegalCorpusChunk.embedding.isnot(None),
                    )
                    .order_by("dist")
                    .limit(1)
                )
            ).first()
            if row is None:
                continue
            _chunk, doc, dist = row
            if dist is None or dist > _CASELAW_MAX_DISTANCE:
                continue
            dedup = f"caselaw:{matter.id}:{doc.id}"
            if not await redis.set(dedup, "1", nx=True, ex=90 * 86400):
                continue
            await notify(
                db, tenant_id=matter.tenant_id, kind="caselaw",
                title=f"⚖ {doc.reference or doc.title[:80]}",
                body=f"{matter.reference}: {doc.title[:180]}",
                url=f"/matters/{matter.id}",
            )
            await db.commit()


async def _file_quality_findings(db: AsyncSession, tenant_id: uuid.UUID) -> list[str]:
    """Deterministic hygiene findings on the tenant's open matters (the Eve
    'file review' idea, without any LLM). Each finding is one short line."""
    now = datetime.now(UTC)
    findings: list[str] = []

    with_opposing = (
        select(MatterParty.matter_id)
        .where(MatterParty.role.in_(["opposing_party", "opposing_counsel"]))
        .distinct()
    )
    no_opposing = (
        await db.execute(
            select(Matter.reference)
            .where(
                Matter.tenant_id == tenant_id,
                Matter.status == "open",
                Matter.id.not_in(with_opposing),
            )
            .limit(8)
        )
    ).scalars().all()
    if no_opposing:
        findings.append(
            f"{len(no_opposing)} lëndë pa palë kundërshtare të regjistruar "
            f"({', '.join(no_opposing[:4])}…)" if len(no_opposing) > 4 else
            f"{len(no_opposing)} lëndë pa palë kundërshtare të regjistruar "
            f"({', '.join(no_opposing)})"
        )

    with_docs = select(Document.matter_id).where(Document.matter_id.is_not(None)).distinct()
    no_docs = (
        await db.execute(
            select(func.count(Matter.id)).where(
                Matter.tenant_id == tenant_id,
                Matter.status == "open",
                Matter.id.not_in(with_docs),
            )
        )
    ).scalar_one()
    if no_docs:
        findings.append(f"{no_docs} lëndë të hapura pa asnjë dokument")

    stale_drafts = (
        await db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.tenant_id == tenant_id,
                Invoice.status == "draft",
                Invoice.created_at < now - timedelta(days=7),
            )
        )
    ).scalar_one()
    if stale_drafts:
        findings.append(f"{stale_drafts} fatura draft më të vjetra se 7 ditë (të padërguara)")

    idle = (
        await db.execute(
            select(func.count(Matter.id)).where(
                Matter.tenant_id == tenant_id,
                Matter.status == "open",
                Matter.updated_at < now - timedelta(days=30),
            )
        )
    ).scalar_one()
    if idle:
        findings.append(f"{idle} lëndë pa asnjë aktivitet prej >30 ditësh")

    return findings


async def run_file_quality_audit(redis: aioredis.Redis) -> None:
    """Nightly file-quality audit (audit 2026-09-18, advancement #7): one
    quiet notification per tenant per day with the hygiene findings. Only
    suggestions (D-044) — nothing is changed."""
    today = date.today().isoformat()
    async with SessionLocal() as db:
        tenants = (
            await db.execute(select(Tenant.id).where(Tenant.status == "active"))
        ).scalars().all()
        for tenant_id in tenants:
            key = f"fileaudit:{tenant_id}:{today}"
            if not await redis.set(key, "1", nx=True, ex=36 * 3600):
                continue
            try:
                findings = await _file_quality_findings(db, tenant_id)
                if not findings:
                    continue
                await notify(
                    db, tenant_id=tenant_id, kind="suggestion",
                    title=f"🗂 Auditimi i dosjeve · {len(findings)} gjetje",
                    body="\n".join(f"• {f}" for f in findings),
                    url="/matters", push=False,
                )
                await db.commit()
            except Exception as exc:
                logger.warning("File-quality audit failed for %s: %s", tenant_id, exc)
                await db.rollback()


async def run_deadline_audit(redis: aioredis.Redis) -> None:
    """Open matters with no upcoming deadline — the classic malpractice
    trap. One quiet notification per tenant per day."""
    today = date.today().isoformat()
    now = datetime.now(UTC)
    async with SessionLocal() as db:
        upcoming = (
            select(Deadline.matter_id)
            .where(Deadline.status == "pending", Deadline.due_at >= now)
            .distinct()
        )
        rows = (
            await db.execute(
                select(Matter.tenant_id, func.count(Matter.id))
                .where(Matter.status == "open", Matter.id.not_in(upcoming))
                .group_by(Matter.tenant_id)
            )
        ).all()
        for tenant_id, count in rows:
            if not count:
                continue
            key = f"dlaudit:{tenant_id}:{today}"
            if not await redis.set(key, "1", nx=True, ex=36 * 3600):
                continue
            await notify(
                db, tenant_id=tenant_id, kind="suggestion",
                title=f"⏰ {count} lëndë të hapura pa afat të ardhshëm",
                body="Kontrollo nëse u mungon ndonjë afat ose seancë.",
                url="/matters", push=False,
            )
            await db.commit()
