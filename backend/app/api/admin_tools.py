"""Admin tools: the audit trail viewer and the full tenant data export.
Both answer procurement questions ("who did what?", "can we take our data?")."""
import csv
import io
import zipfile
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import (
    AuditLog,
    Contact,
    Deadline,
    Document,
    Expense,
    Invoice,
    Matter,
    Task,
    TimeEntry,
    User,
)
from app.services import storage
from app.services.audit import log_action

router = APIRouter(tags=["admin-tools"])


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")


@router.get("/audit-log")
async def audit_log(
    action: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(user)
    stmt = select(AuditLog).where(AuditLog.tenant_id == user.tenant_id)
    if action:
        stmt = stmt.where(AuditLog.action.like(f"{action}%"))
    stmt = stmt.order_by(AuditLog.at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    user_ids = {r.user_id for r in rows if r.user_id}
    names: dict = {}
    if user_ids:
        for u in (
            await db.execute(select(User).where(User.id.in_(user_ids)))
        ).scalars():
            names[u.id] = u.full_name

    return [
        {
            "id": str(r.id),
            "at": r.at.isoformat(),
            "user": names.get(r.user_id),
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "details": r.details or {},
        }
        for r in rows
    ]


def _csv(headers: list[str], rows: list[list]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return buf.getvalue()


@router.get("/export/tenant")
async def export_tenant(
    include_documents: bool = True,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full data export: CSVs of every core table plus the decrypted documents.
    The exit guarantee every serious buyer asks about."""
    _require_admin(user)
    tid = user.tenant_id

    async def rows(model):
        return (await db.execute(select(model).where(model.tenant_id == tid))).scalars().all()

    matters = await rows(Matter)
    contacts = await rows(Contact)
    deadlines = await rows(Deadline)
    time_entries = await rows(TimeEntry)
    expenses = await rows(Expense)
    invoices = (
        await db.execute(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.tenant_id == tid)
        )
    ).scalars().all()
    tasks = await rows(Task)
    documents = await rows(Document)

    contact_names = {c.id: c.display_name for c in contacts}
    matter_refs = {m.id: m.reference for m in matters}

    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("lendet.csv", _csv(
            ["referenca", "titulli", "statusi", "fusha", "gjykata", "nr_rendor",
             "klienti", "hapur_me", "pershkrimi"],
            [[m.reference, m.title, m.status, m.practice_area, m.court_name or "",
              m.court_case_number or "", contact_names.get(m.client_id, ""),
              m.opened_on.isoformat() if m.opened_on else "", m.description or ""]
             for m in matters],
        ))
        zf.writestr("kontaktet.csv", _csv(
            ["emri", "lloji", "email", "telefoni", "adresa", "nr_identifikues"],
            [[c.display_name, c.kind, c.email or "", c.phone or "",
              c.address or "", c.national_id or ""] for c in contacts],
        ))
        zf.writestr("afatet.csv", _csv(
            ["lenda", "titulli", "lloji", "skadon", "statusi", "baza_ligjore"],
            [[matter_refs.get(d.matter_id, ""), d.title, d.kind,
              d.due_at.isoformat(), d.status, d.legal_basis or ""] for d in deadlines],
        ))
        zf.writestr("oret.csv", _csv(
            ["lenda", "data", "minuta", "pershkrimi", "e_faturueshme", "tarifa", "e_faturuar"],
            [[matter_refs.get(t.matter_id, ""), t.started_at.isoformat(), t.minutes,
              t.description, t.billable, str(t.hourly_rate or ""),
              bool(t.invoice_id)] for t in time_entries],
        ))
        zf.writestr("shpenzimet.csv", _csv(
            ["lenda", "data", "pershkrimi", "kategoria", "shuma", "e_faturuar"],
            [[matter_refs.get(e.matter_id, ""), e.incurred_on.isoformat(),
              e.description, e.category, str(e.amount), bool(e.invoice_id)]
             for e in expenses],
        ))
        zf.writestr("faturat.csv", _csv(
            ["numri", "lenda", "klienti", "statusi", "leshuar", "paguar",
             "nentotali", "tvsh_pct", "totali"],
            [[i.number, matter_refs.get(i.matter_id, ""),
              contact_names.get(i.contact_id, ""), i.status,
              i.issued_on.isoformat() if i.issued_on else "",
              i.paid_on.isoformat() if i.paid_on else "",
              str(i.total), i.vat_rate, str(i.total_with_vat)] for i in invoices],
        ))
        zf.writestr("detyrat.csv", _csv(
            ["titulli", "lenda", "statusi", "prioriteti", "afati"],
            [[t.title, matter_refs.get(t.matter_id, ""), t.status, t.priority,
              t.due_date.isoformat() if t.due_date else ""] for t in tasks],
        ))
        if include_documents:
            for d in documents:
                if not d.is_latest:
                    continue
                try:
                    content = storage.load_file(d.storage_path, d.encrypted)
                except Exception:
                    continue
                ref = matter_refs.get(d.matter_id, "pa-lende")
                zf.writestr(f"dokumentet/{ref}/{d.filename}", content)

    await log_action(
        db, tenant_id=tid, user_id=user.id, action="tenant.export",
        entity_type="tenant", entity_id=str(tid),
        details={"documents": include_documents},
    )
    await db.commit()

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M")
    return Response(
        content=zbuf.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="boralaw-eksporti-{stamp}.zip"'
        },
    )
