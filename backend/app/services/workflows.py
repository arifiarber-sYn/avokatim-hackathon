"""Expert workflows on a matter (audit 2026-09-18, advancement #6).

Fixed, named litigation routines (appeal analysis, filing compliance,
evidence map) executed step by step with live SSE progress — the Vincent /
AVOKATI W1–W5 pattern. Definitions are DATA in seeds/workflow_defs.py
(jurisdiction-specific, XK first); this module only resolves context,
drives the LLM through app/llm, verifies citations (v2) and saves the
result as a MatterNote + audit entry. No other writes — D-044 stands.
"""
import logging
import uuid
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import get_provider
from app.llm.base import ChatMessage
from app.models import Deadline, Jurisdiction, Matter, MatterNote, User
from app.models.jurisdiction import DeadlineRule
from app.seeds.workflow_defs import get_workflow
from app.services import rag
from app.services.assistant import build_matter_context
from app.services.audit import log_action
from app.services.citation_check import verify_citations

logger = logging.getLogger(__name__)

WORKFLOW_KINDS = ("appeal", "compliance", "evidence")

_LANG_NAMES = {
    "sq": "shqip", "sr": "srpski", "tr": "Türkçe", "bs": "bosanski",
    "en": "English", "zh": "中文", "de": "Deutsch",
}


async def _deadline_rules_text(db: AsyncSession, jurisdiction_id: uuid.UUID) -> str:
    rules = (
        await db.execute(
            select(DeadlineRule)
            .where(DeadlineRule.jurisdiction_id == jurisdiction_id)
            .order_by(DeadlineRule.practice_area, DeadlineRule.code)
        )
    ).scalars().all()
    lines = []
    for r in rules:
        name = r.name.get("sq") or next(iter(r.name.values()), r.code)
        lines.append(
            f"- [{r.practice_area or '—'}] {name}: {r.days} "
            f"{'ditë pune' if r.day_type == 'business' else 'muaj' if r.day_type == 'months' else 'ditë'} "
            f"nga '{r.trigger_event}'"
            + (f" ({r.legal_basis})" if r.legal_basis else "")
        )
    return "\n".join(lines) or "—"


async def _upcoming_text(db: AsyncSession, matter_id: uuid.UUID) -> str:
    rows = (
        await db.execute(
            select(Deadline)
            .where(Deadline.matter_id == matter_id, Deadline.status == "pending")
            .order_by(Deadline.due_at)
            .limit(20)
        )
    ).scalars().all()
    return "\n".join(
        f"- {d.due_at:%Y-%m-%d}: {d.title}"
        + (f" ({d.legal_basis})" if d.legal_basis else "")
        for d in rows
    ) or "—"


async def _documents_text(db: AsyncSession, matter_id: uuid.UUID) -> str:
    docs = await rag.matter_documents_full(db, matter_id, char_budget=36_000)
    return "\n\n".join(
        f"=== {d['doc_title']} ===\n{d['text']}" for d in docs
    ) or "— (lënda s'ka dokumente të indeksuara)"


async def workflow_stream(
    db: AsyncSession,
    *,
    matter: Matter,
    kind: str,
    user: User,
    provider_name: str | None,
    language: str | None = None,
) -> AsyncIterator[dict]:
    """Yields: plan, step(running/done/failed), result (per step),
    citation_check, done{note_id}. The combined output is saved as a
    MatterNote and audited."""
    jur = await db.get(Jurisdiction, matter.jurisdiction_id) if matter.jurisdiction_id else None
    jur_code = jur.code if jur else "XK"
    defn = get_workflow(kind, jur_code)
    if defn is None:
        yield {"type": "error", "detail": f"Unknown workflow '{kind}'"}
        return

    yield {
        "type": "plan",
        "workflow": kind,
        "name": defn["name"],
        "steps": [{"id": s["id"], "label": s["label"]} for s in defn["steps"]],
    }

    # Context builders — resolved once, reused across steps that need them
    ctx_cache: dict[str, str] = {}

    async def ctx(name: str) -> str:
        if name in ctx_cache:
            return ctx_cache[name]
        if name == "matter_context":
            val = await build_matter_context(db, matter.id)
        elif name == "documents":
            val = await _documents_text(db, matter.id)
        elif name == "deadline_rules":
            val = (
                await _deadline_rules_text(db, matter.jurisdiction_id)
                if matter.jurisdiction_id else "—"
            )
        elif name == "upcoming":
            val = await _upcoming_text(db, matter.id)
        elif name == "language_hint":
            val = (
                f"\nPërgjigju në gjuhën: {_LANG_NAMES.get(language, language)}."
                if language and language != "sq" else ""
            )
        else:
            val = ""
        ctx_cache[name] = val
        return val

    provider = get_provider(provider_name)
    history: list[ChatMessage] = []
    outputs: list[tuple[str, str]] = []

    for i, step in enumerate(defn["steps"]):
        yield {"type": "step", "index": i, "status": "running", "label": step["label"]}
        try:
            fmt = {name: await ctx(name) for name in step["needs"]}
            fmt["jurisdiction"] = jur_code
            prompt = step["prompt"].format(**fmt)
            messages = [*history, ChatMessage(role="user", content=prompt)]
            result = await provider.chat(messages)
            answer = result.content
            # steps build on each other: keep the exchange in-history
            history.extend([
                ChatMessage(role="user", content=prompt),
                ChatMessage(role="assistant", content=answer),
            ])
            outputs.append((step["label"], answer))
            yield {"type": "result", "index": i, "content": answer}
            yield {"type": "step", "index": i, "status": "done"}
        except Exception as exc:
            logger.warning("workflow %s step %s failed: %s", kind, step["id"], exc)
            yield {"type": "step", "index": i, "status": "failed", "detail": str(exc)[:200]}

    if not outputs:
        yield {"type": "error", "detail": "Workflow produced no output"}
        return

    combined = "\n\n".join(f"## {label}\n\n{text}" for label, text in outputs)

    # Citation verification report (v2) travels with the result
    checked: list[dict] = []
    try:
        checked = await verify_citations(db, matter.jurisdiction_id, combined)
    except Exception:
        logger.exception("workflow citation verification failed")
    if checked:
        yield {"type": "citation_check", "citations": checked}

    icon = {"verified": "✓", "approx": "≈", "law_found": "§", "unverified": "?"}
    report = "\n".join(
        f"- {icon[c['status']]} {c['cite']}" + (f" — {c['note']}" if c.get("note") else "")
        for c in checked
    )
    body = (
        f"[Workflow: {defn['name']}]\n\n{combined}"
        + (f"\n\n---\nVerifikimi i citimeve:\n{report}" if report else "")
    )
    note = MatterNote(
        tenant_id=matter.tenant_id, matter_id=matter.id, author_id=user.id, body=body
    )
    db.add(note)
    await db.flush()
    await log_action(
        db, tenant_id=matter.tenant_id, user_id=user.id, action="matter.workflow",
        entity_type="matter", entity_id=str(matter.id),
        details={"workflow": kind, "steps": len(outputs),
                 "unverified": sum(1 for c in checked if c["status"] == "unverified")},
    )
    await db.commit()
    yield {"type": "done", "note_id": str(note.id)}
