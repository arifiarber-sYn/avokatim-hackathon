"""Consent checks (Law 06/L-082 art. 7): a contact has consent of a given
kind when there is a granted, non-revoked record."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConsentRecord


async def has_consent(db: AsyncSession, contact_id: uuid.UUID, kind: str) -> bool:
    row = (
        await db.execute(
            select(ConsentRecord.id).where(
                ConsentRecord.contact_id == contact_id,
                ConsentRecord.kind == kind,
                ConsentRecord.revoked_at.is_(None),
            ).limit(1)
        )
    ).scalar_one_or_none()
    return row is not None


async def grant_consent(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    kind: str,
    method: str,
    ip: str | None = None,
    notes: str | None = None,
) -> ConsentRecord:
    """Idempotent: returns the active record if one already exists."""
    existing = (
        await db.execute(
            select(ConsentRecord).where(
                ConsentRecord.contact_id == contact_id,
                ConsentRecord.kind == kind,
                ConsentRecord.revoked_at.is_(None),
            ).limit(1)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    record = ConsentRecord(
        tenant_id=tenant_id,
        contact_id=contact_id,
        kind=kind,
        granted_at=datetime.now(UTC),
        method=method,
        ip=ip,
        notes=notes,
    )
    db.add(record)
    await db.flush()
    return record


async def revoke_consent(
    db: AsyncSession, *, contact_id: uuid.UUID, kind: str
) -> int:
    """Marks all active records of this kind revoked; returns how many."""
    rows = (
        await db.execute(
            select(ConsentRecord).where(
                ConsentRecord.contact_id == contact_id,
                ConsentRecord.kind == kind,
                ConsentRecord.revoked_at.is_(None),
            )
        )
    ).scalars().all()
    now = datetime.now(UTC)
    for r in rows:
        r.revoked_at = now
    return len(rows)
