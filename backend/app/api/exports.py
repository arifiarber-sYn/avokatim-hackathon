"""Accounting exports (D-037): DATEV EXTF for German offices — invoices and
payments of a period as a Buchungsstapel the Steuerberater imports directly."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, Invoice, Tenant, User
from app.services.audit import log_action
from app.services.datev import (
    DEFAULT_DEBTOR_ACCOUNT,
    DEFAULT_REVENUE_ACCOUNT,
    DatevConfig,
    bookings_for_invoices,
    build_extf,
)

router = APIRouter(prefix="/export", tags=["exports"])


@router.get("/datev")
async def datev_export(
    date_from: date,
    date_to: date,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if date_to < date_from or (date_to - date_from).days > 400:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid period")
    tenant = await db.get(Tenant, user.tenant_id)
    if tenant.country != "DE":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "DATEV export is for German offices")

    config = DatevConfig(
        consultant_no=tenant.datev_consultant_no or "",
        client_no=tenant.datev_client_no or "",
        revenue_account=tenant.datev_revenue_account or DEFAULT_REVENUE_ACCOUNT,
        debtor_account=tenant.datev_debtor_account or DEFAULT_DEBTOR_ACCOUNT,
    )
    invoices = (
        (
            await db.execute(
                select(Invoice)
                .options(selectinload(Invoice.items))
                .where(
                    Invoice.tenant_id == user.tenant_id,
                    Invoice.status.in_(("sent", "paid")),
                )
            )
        )
        .scalars()
        .all()
    )
    contact_ids = {inv.contact_id for inv in invoices if inv.contact_id}
    client_names: dict = {}
    if contact_ids:
        rows = (
            await db.execute(
                select(Contact.id, Contact.display_name).where(Contact.id.in_(contact_ids))
            )
        ).all()
        client_names = dict(rows)
    bookings = bookings_for_invoices(
        invoices, config, date_from, date_to, client_names
    )
    csv_bytes = build_extf(bookings, config, date_from, date_to)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="export.datev",
        entity_type="tenant", entity_id=str(tenant.id),
        details={"from": date_from.isoformat(), "to": date_to.isoformat(),
                 "bookings": len(bookings)},
    )
    await db.commit()
    filename = f"EXTF_Buchungsstapel_{date_from:%Y%m%d}-{date_to:%Y%m%d}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=windows-1252",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/accounting")
async def accounting_export(
    date_from: date,
    date_to: date,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generic accountant CSV (DE→XK parity, DATEV analog): one row per
    non-draft invoice issued or paid in the period. Stable snake_case
    headers, semicolon-separated, UTF-8 BOM so Excel opens it correctly.
    Available to every office regardless of country."""
    import csv
    import io

    from sqlalchemy.orm import selectinload

    if date_to < date_from or (date_to - date_from).days > 400:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid period")

    invoices = (
        (
            await db.execute(
                select(Invoice)
                .options(selectinload(Invoice.items))
                .where(
                    Invoice.tenant_id == user.tenant_id,
                    Invoice.status.in_(("sent", "paid")),
                )
                .order_by(Invoice.number)
            )
        )
        .scalars()
        .all()
    )
    invoices = [
        inv
        for inv in invoices
        if (inv.issued_on and date_from <= inv.issued_on <= date_to)
        or (inv.paid_on and date_from <= inv.paid_on <= date_to)
    ]

    contact_ids = {inv.contact_id for inv in invoices if inv.contact_id}
    client_names: dict = {}
    if contact_ids:
        rows = (
            await db.execute(
                select(Contact.id, Contact.display_name).where(Contact.id.in_(contact_ids))
            )
        ).all()
        client_names = dict(rows)

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow([
        "invoice_number", "issued_on", "due_on", "client", "currency",
        "net_amount", "vat_rate_percent", "vat_amount", "gross_amount",
        "status", "paid_on", "payment_reference",
    ])
    for inv in invoices:
        writer.writerow([
            inv.number,
            inv.issued_on.isoformat() if inv.issued_on else "",
            inv.due_on.isoformat() if inv.due_on else "",
            client_names.get(inv.contact_id, ""),
            inv.currency,
            f"{inv.total:.2f}",
            inv.vat_rate or 0,
            f"{inv.vat_amount:.2f}",
            f"{inv.total_with_vat:.2f}",
            inv.status,
            inv.paid_on.isoformat() if inv.paid_on else "",
            inv.payment_reference or "",
        ])

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="export.accounting",
        entity_type="tenant", entity_id=str(user.tenant_id),
        details={"from": date_from.isoformat(), "to": date_to.isoformat(),
                 "invoices": len(invoices)},
    )
    await db.commit()
    filename = f"fatura_{date_from:%Y%m%d}-{date_to:%Y%m%d}.csv"
    return Response(
        content="\ufeff" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
