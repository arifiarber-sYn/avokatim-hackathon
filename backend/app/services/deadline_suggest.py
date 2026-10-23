"""Document/email scan → deadline proposals (D-043, F4 back-office agents).

When a document with extracted text lands in a matter (upload or email
attachment), a background task asks the LLM (through the provider
abstraction only) for procedural dates, matches them against the matter
jurisdiction's DeadlineRule rows, and stores DeadlineSuggestion rows.
Nothing is ever auto-created: the lawyer accepts or dismisses each
suggestion (same model as TimeSuggestion).
"""
import asyncio
import logging
import re
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.llm import LOCAL_PINNED
from app.models import (
    DeadlineRule,
    DeadlineSuggestion,
    Document,
    Matter,
    Tenant,
    User,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)

MIN_TEXT_CHARS = 200
MAX_SUGGESTIONS = 5


def _tokens(value: str | None) -> set[str]:
    return {w.lower() for w in re.findall(r"[0-9A-Za-zÀ-ÿẞäöüß§]+", value or "") if len(w) > 1}


def match_rule(rules: list[DeadlineRule], legal_basis: str | None, title: str | None):
    """Best-effort match of an extracted deadline to a procedural rule.

    Signals: overlap between the extracted legal basis and the rule's
    legal_basis (statute + article tokens, e.g. "ZPO"/"517"), plus overlap
    between the extracted title and the rule's localized names. Returns the
    rule only when the evidence is specific enough (≥ 2 basis tokens, e.g.
    statute AND article) — a vague match is worse than none.
    """
    want_basis = _tokens(legal_basis)
    want_title = _tokens(title)
    best, best_score = None, 0
    for rule in rules:
        score = 0
        rule_basis = _tokens(rule.legal_basis)
        basis_hits = len(want_basis & rule_basis)
        if basis_hits >= 2:
            score += 2 * basis_hits
        name_tokens: set[str] = set()
        for name in (rule.name or {}).values():
            name_tokens |= _tokens(name)
        # Long tokens (German compounds like "Kündigungsschutzklage") are
        # distinctive enough to carry a match on their own.
        score += sum(2 if len(t) >= 10 else 1 for t in want_title & name_tokens)
        if score > best_score:
            best, best_score = rule, score
    return best if best_score >= 2 else None


async def _create_suggestions(
    db: AsyncSession, doc: Document, matter: Matter, items: list[dict], source: str
) -> int:
    rules = (
        (
            await db.execute(
                select(DeadlineRule).where(
                    DeadlineRule.jurisdiction_id == matter.jurisdiction_id
                )
            )
        )
        .scalars()
        .all()
    )
    created = 0
    for item in items[:MAX_SUGGESTIONS * 2]:
        if created >= MAX_SUGGESTIONS:
            break
        title = str(item.get("title") or "").strip()[:500]
        if not title:
            continue
        due = _parse_date(item.get("date"))
        trigger = _parse_date(item.get("trigger_date"))
        rule = match_rule(rules, item.get("legal_basis"), title)
        # A suggestion must be actionable: a concrete date, or a rule the
        # engine can compute from (with or without a trigger — the lawyer
        # can fill the trigger date on accept).
        if due is None and rule is None:
            continue
        kind = item.get("kind") if item.get("kind") in ("deadline", "hearing", "meeting") else "deadline"
        db.add(
            DeadlineSuggestion(
                tenant_id=matter.tenant_id,
                matter_id=matter.id,
                document_id=doc.id,
                source=source,
                kind=kind,
                title=title,
                due_date=due,
                rule_id=rule.id if rule else None,
                trigger_date=trigger,
                legal_basis=(item.get("legal_basis") or (rule.legal_basis if rule else None) or "")[:255] or None,
                confidence=item.get("confidence") if item.get("confidence") in ("high", "medium", "low") else "low",
            )
        )
        created += 1
    return created


def _parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


async def scan_document(document_id: uuid.UUID, source: str = "document") -> int:
    """Extract deadline proposals for one document. Runs in its own session
    (background task). Returns the number of suggestions created."""
    from app.services.assistant import extract_deadlines_from_text

    async with SessionLocal() as db:
        doc = await db.get(Document, document_id)
        if doc is None or not doc.matter_id:
            return 0
        if not doc.text_content or len(doc.text_content.strip()) < MIN_TEXT_CHARS:
            return 0
        existing = (
            await db.execute(
                select(func.count(DeadlineSuggestion.id)).where(
                    DeadlineSuggestion.document_id == document_id
                )
            )
        ).scalar_one()
        if existing:
            return 0  # already scanned (e.g. re-poll)
        matter = await db.get(Matter, doc.matter_id)
        if matter is None:
            return 0
        tenant = await db.get(Tenant, doc.tenant_id)
        # BRAK/DSGVO gate: office forbids external AI → local provider only
        provider = LOCAL_PINNED if tenant and not tenant.allow_external_ai else None

        try:
            items = await extract_deadlines_from_text(doc.text_content, provider)
        except Exception as exc:  # noqa: BLE001 — background job must not crash
            logger.warning(
                "Deadline scan failed for document %s: %r", document_id, exc
            )
            return 0

        created = await _create_suggestions(db, doc, matter, items, source)
        if created:
            await log_action(
                db, tenant_id=doc.tenant_id, user_id=None,
                action="ai.deadline_suggest", entity_type="document",
                entity_id=str(doc.id),
                details={"suggestions": created, "source": source},
            )
            from app.i18n import pick_locale, tr
            from app.services.notification_center import notify as notify_center

            responsible = (
                await db.get(User, matter.responsible_user_id)
                if matter.responsible_user_id
                else None
            )
            loc = pick_locale(responsible.locale if responsible else None)
            await notify_center(
                db, tenant_id=doc.tenant_id, kind="suggestion",
                title=tr(loc, "ntf_suggestions_title", n=created, ref=matter.reference),
                body=doc.filename, url=f"/matters/{matter.id}",
            )
        await db.commit()
        logger.info(
            "Deadline scan of document %s: %s suggestion(s)", document_id, created
        )
        return created


def scan_document_background(document_id: uuid.UUID, source: str = "document") -> None:
    """Fire-and-forget entry point for request handlers / the email poller."""

    async def _run() -> None:
        try:
            await scan_document(document_id, source)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Deadline scan task failed: %s", exc)

    asyncio.create_task(_run())
