"""Conflict-of-interest check: before accepting a case, search existing
contacts and matters for the prospective client and opposing parties."""
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact, Matter, MatterParty


async def check_conflicts(
    db: AsyncSession, tenant_id: uuid.UUID, names: list[str]
) -> dict:
    """Returns {"has_conflicts": bool, "hits": [...]} — every existing contact
    whose name matches one of the given names, with the matters and roles in
    which they appear."""
    hits = []
    for name in names:
        needle = name.strip()
        if not needle:
            continue
        contacts = (
            (
                await db.execute(
                    select(Contact).where(
                        Contact.tenant_id == tenant_id,
                        func.lower(Contact.display_name).contains(needle.lower()),
                    )
                )
            )
            .scalars()
            .all()
        )
        for contact in contacts:
            roles = (
                await db.execute(
                    select(MatterParty.role, Matter.reference, Matter.title, Matter.status)
                    .join(Matter, Matter.id == MatterParty.matter_id)
                    .where(MatterParty.contact_id == contact.id)
                )
            ).all()
            client_of = (
                await db.execute(
                    select(Matter.reference, Matter.title, Matter.status).where(
                        Matter.client_id == contact.id
                    )
                )
            ).all()
            hits.append(
                {
                    "searched_name": needle,
                    "contact_id": str(contact.id),
                    "contact_name": contact.display_name,
                    "appears_in": [
                        {"role": r, "matter": ref, "title": t, "status": s}
                        for r, ref, t, s in roles
                    ]
                    + [
                        {"role": "client", "matter": ref, "title": t, "status": s}
                        for ref, t, s in client_of
                    ],
                }
            )
    return {"has_conflicts": any(h["appears_in"] for h in hits), "hits": hits}
