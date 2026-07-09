"""Global search: one query across matters, contacts, documents and invoices.
Respects restricted-matter visibility for the current user."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import restricted_visibility_filter
from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, Document, Invoice, Matter, User

router = APIRouter(prefix="/search", tags=["search"])

_LIMIT = 8


@router.get("")
async def global_search(
    q: str = Query(min_length=2, max_length=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    needle = f"%{q.lower()}%"

    matters = (
        await db.execute(
            select(Matter)
            .where(
                Matter.tenant_id == user.tenant_id,
                restricted_visibility_filter(user),
                or_(
                    func.lower(Matter.title).like(needle),
                    func.lower(Matter.reference).like(needle),
                    func.lower(func.coalesce(Matter.description, "")).like(needle),
                    func.lower(func.coalesce(Matter.court_case_number, "")).like(needle),
                ),
            )
            .order_by(Matter.created_at.desc())
            .limit(_LIMIT)
        )
    ).scalars().all()

    contacts = (
        await db.execute(
            select(Contact)
            .where(
                Contact.tenant_id == user.tenant_id,
                or_(
                    func.lower(Contact.display_name).like(needle),
                    func.lower(func.coalesce(Contact.email, "")).like(needle),
                    func.coalesce(Contact.phone, "").like(f"%{q}%"),
                ),
            )
            .order_by(Contact.display_name)
            .limit(_LIMIT)
        )
    ).scalars().all()

    # Documents: match filename or extracted text, but only in visible matters
    visible_matters = select(Matter.id).where(
        Matter.tenant_id == user.tenant_id, restricted_visibility_filter(user)
    )
    documents = (
        await db.execute(
            select(Document)
            .where(
                Document.tenant_id == user.tenant_id,
                Document.is_latest.is_(True),
                or_(Document.matter_id.is_(None), Document.matter_id.in_(visible_matters)),
                or_(
                    func.lower(Document.filename).like(needle),
                    func.lower(func.coalesce(Document.text_content, "")).like(needle),
                ),
            )
            .order_by(Document.created_at.desc())
            .limit(_LIMIT)
        )
    ).scalars().all()

    invoices = (
        await db.execute(
            select(Invoice)
            .where(
                Invoice.tenant_id == user.tenant_id,
                func.lower(Invoice.number).like(needle),
            )
            .order_by(Invoice.created_at.desc())
            .limit(_LIMIT)
        )
    ).scalars().all()

    def _snippet(text: str | None) -> str | None:
        if not text:
            return None
        pos = text.lower().find(q.lower())
        if pos < 0:
            return None
        start = max(0, pos - 60)
        return ("…" if start else "") + text[start:pos + len(q) + 60].replace("\n", " ") + "…"

    return {
        "matters": [
            {
                "id": str(m.id),
                "reference": m.reference,
                "title": m.title,
                "status": m.status,
            }
            for m in matters
        ],
        "contacts": [
            {
                "id": str(c.id),
                "display_name": c.display_name,
                "email": c.email,
                "kind": c.kind,
            }
            for c in contacts
        ],
        "documents": [
            {
                "id": str(d.id),
                "matter_id": str(d.matter_id) if d.matter_id else None,
                "filename": d.filename,
                "snippet": _snippet(d.text_content),
            }
            for d in documents
        ],
        "invoices": [
            {
                "id": str(i.id),
                "number": i.number,
                "status": i.status,
                "matter_id": str(i.matter_id) if i.matter_id else None,
            }
            for i in invoices
        ],
    }
