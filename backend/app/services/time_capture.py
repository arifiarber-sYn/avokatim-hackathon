"""Passive time capture (the Smokeball model).

Reads the append-only audit trail, groups matter-related activity per
(matter, user, day) and turns it into TimeSuggestion rows the lawyer can
accept (creates a real TimeEntry) or dismiss. Nothing is billed without an
explicit accept, and the generator is idempotent: a (matter, user, day) that
already has a suggestion — in any status — is never re-suggested.
"""
import logging
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, Document, Matter, TimeSuggestion

logger = logging.getLogger(__name__)

# Heuristic minutes credited per audit action. Deliberately conservative —
# the suggestion is a floor the lawyer adjusts, not a claim.
ACTION_MINUTES: dict[str, int] = {
    "document.upload": 6,
    "document.summarize": 5,
    "document.review_request": 3,
    "template.render_to_matter": 10,
    "assistant.prepare_matter": 15,
    "assistant.hearing_prep": 15,
    "ai.extract_deadlines": 5,
    "deadline.bulk_create_ai": 3,
    "email.ingested": 4,
}

# Human-readable (Albanian) labels used in the suggestion description; the
# lawyer edits the final TimeEntry text anyway.
_ACTION_LABEL = {
    "document.upload": "dokumente të ngarkuara",
    "document.summarize": "përmbledhje dokumentesh",
    "document.review_request": "kërkesa recensioni",
    "template.render_to_matter": "shkresa të gjeneruara",
    "assistant.prepare_matter": "përgatitje lënde me Avën",
    "assistant.hearing_prep": "përgatitje seance me Avën",
    "ai.extract_deadlines": "afate të nxjerra me AI",
    "deadline.bulk_create_ai": "afate të regjistruara",
    "email.ingested": "emaila të arkivuar",
}

MAX_SUGGESTED_MINUTES = 120
LOOKBACK_DAYS = 7


async def _matter_for_log(db: AsyncSession, log: AuditLog) -> uuid.UUID | None:
    """Resolve which matter an audit row belongs to."""
    if not log.entity_id:
        return None
    try:
        entity_uuid = uuid.UUID(log.entity_id)
    except ValueError:
        return None
    if log.entity_type == "matter":
        return entity_uuid
    if log.entity_type == "document":
        doc = await db.get(Document, entity_uuid)
        return doc.matter_id if doc else None
    return None


async def generate_suggestions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    lookback_days: int = LOOKBACK_DAYS,
) -> int:
    """Scan recent complete days of audit activity for a tenant and insert
    pending TimeSuggestion rows. Returns the number created."""
    today = date.today()
    since = today - timedelta(days=lookback_days)
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.user_id.is_not(None),
            AuditLog.action.in_(ACTION_MINUTES.keys()),
            AuditLog.at >= since,
            func.date(AuditLog.at) < today,  # only complete days
        )
        .order_by(AuditLog.at)
    )
    logs = (await db.execute(stmt)).scalars().all()
    if not logs:
        return 0

    # Group actions into (matter, user, day) windows
    windows: dict[tuple[uuid.UUID, uuid.UUID, date], dict[str, int]] = {}
    matter_cache: dict[str, uuid.UUID | None] = {}
    for log in logs:
        cache_key = f"{log.entity_type}:{log.entity_id}"
        if cache_key not in matter_cache:
            matter_cache[cache_key] = await _matter_for_log(db, log)
        matter_id = matter_cache[cache_key]
        if matter_id is None:
            continue
        key = (matter_id, log.user_id, log.at.date())
        windows.setdefault(key, {})
        windows[key][log.action] = windows[key].get(log.action, 0) + 1

    if not windows:
        return 0

    # Idempotency: skip windows that already have a suggestion (any status)
    existing = (
        await db.execute(
            select(
                TimeSuggestion.matter_id, TimeSuggestion.user_id, TimeSuggestion.day
            ).where(
                TimeSuggestion.tenant_id == tenant_id,
                TimeSuggestion.day >= since,
            )
        )
    ).all()
    seen = {(m, u, d) for m, u, d in existing}

    # Matters may have been deleted since the audit rows were written
    matter_ids = {m for (m, _, _) in windows}
    live_matters = set(
        (
            await db.execute(
                select(Matter.id).where(
                    Matter.id.in_(matter_ids), Matter.tenant_id == tenant_id
                )
            )
        ).scalars()
    )

    created = 0
    for (matter_id, user_id, day), counts in windows.items():
        if (matter_id, user_id, day) in seen or matter_id not in live_matters:
            continue
        minutes = min(
            sum(ACTION_MINUTES[a] * n for a, n in counts.items()),
            MAX_SUGGESTED_MINUTES,
        )
        if minutes <= 0:
            continue
        parts = [
            f"{n}× {_ACTION_LABEL.get(a, a)}" for a, n in sorted(counts.items())
        ]
        db.add(
            TimeSuggestion(
                tenant_id=tenant_id,
                matter_id=matter_id,
                user_id=user_id,
                source="activity",
                day=day,
                suggested_minutes=minutes,
                description="Aktivitet i regjistruar: " + ", ".join(parts),
            )
        )
        created += 1
    if created:
        logger.info("time-capture: %s suggestions for tenant %s", created, tenant_id)
    return created
