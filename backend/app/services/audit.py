import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip_address,
        )
    )
