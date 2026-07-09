"""AML endpoints (Law No. 05/L-096): NjIF-K indicator checklist per matter
and internal suspicion reports exported as PDF for filing with FIU-Kosovo.
Indicators are jurisdiction DATA (seeds), never hardcoded logic."""
import html
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, Matter, SuspicionReport, Tenant, TrustTransaction, User
from app.seeds.kosovo import XK_AML_INDICATORS, XK_AML_SCOPE_HINT
from app.services.audit import log_action

router = APIRouter(prefix="/aml", tags=["aml"])

# Indicator sets per jurisdiction code — extend with data, not code
INDICATORS = {"XK": XK_AML_INDICATORS}
SCOPE_HINTS = {"XK": XK_AML_SCOPE_HINT}

# Cash threshold of Law 05/L-096 (art. 25): warn at/above this amount
CASH_THRESHOLD_EUR = 10_000


@router.get("/indicators")
async def list_indicators(jurisdiction: str = "XK"):
    return {
        "jurisdiction": jurisdiction,
        "scope_hint": SCOPE_HINTS.get(jurisdiction, {}),
        "cash_threshold_eur": CASH_THRESHOLD_EUR,
        "indicators": INDICATORS.get(jurisdiction, []),
    }


# ---------- Per-matter checklist (state lives in Matter.extra["aml"]) ----------

class ChecklistIn(BaseModel):
    # {"in_scope": true, "checked": {"aml.cash_large": true, ...}, "notes": "..."}
    in_scope: bool
    checked: dict[str, bool] = {}
    notes: str | None = None


async def _owned_matter(db: AsyncSession, user: User, matter_id: uuid.UUID) -> Matter:
    matter = await db.get(Matter, matter_id)
    if matter is None or matter.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Matter not found")
    return matter


@router.get("/matters/{matter_id}/checklist")
async def get_checklist(
    matter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    matter = await _owned_matter(db, user, matter_id)
    saved = (matter.extra or {}).get("aml", {})
    # Suggest scope when the matter manages client funds via the trust ledger
    has_trust = (
        await db.execute(
            select(TrustTransaction.id)
            .where(TrustTransaction.matter_id == matter.id).limit(1)
        )
    ).scalar_one_or_none() is not None
    return {
        "in_scope": saved.get("in_scope", has_trust),
        "suggested_in_scope": has_trust,
        "checked": saved.get("checked", {}),
        "notes": saved.get("notes"),
    }


@router.put("/matters/{matter_id}/checklist")
async def save_checklist(
    matter_id: uuid.UUID,
    body: ChecklistIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    matter = await _owned_matter(db, user, matter_id)
    extra = dict(matter.extra or {})
    extra["aml"] = {
        "in_scope": body.in_scope,
        "checked": {k: v for k, v in body.checked.items() if v},
        "notes": body.notes,
        "updated_at": datetime.now(UTC).isoformat(),
        "updated_by": str(user.id),
    }
    matter.extra = extra
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="aml.checklist",
        entity_type="matter", entity_id=str(matter.id),
        details={"in_scope": body.in_scope, "flagged": len(extra["aml"]["checked"])},
    )
    await db.commit()
    return extra["aml"]


# ---------- Suspicion reports ----------

class ReportIn(BaseModel):
    matter_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    indicators: list[str] = []
    description: str


class ReportOut(BaseModel):
    id: uuid.UUID
    matter_id: uuid.UUID | None
    contact_id: uuid.UUID | None
    indicators: list
    description: str
    status: str
    submitted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/reports", response_model=list[ReportOut])
async def list_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return (
        await db.execute(
            select(SuspicionReport)
            .where(SuspicionReport.tenant_id == user.tenant_id)
            .order_by(SuspicionReport.created_at.desc())
        )
    ).scalars().all()


@router.post("/reports", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def create_report(
    body: ReportIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.description.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Description required")
    report = SuspicionReport(
        tenant_id=user.tenant_id,
        matter_id=body.matter_id,
        contact_id=body.contact_id,
        created_by_id=user.id,
        indicators=body.indicators,
        description=body.description.strip(),
    )
    db.add(report)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="aml.report_create",
        entity_type="suspicion_report", entity_id=str(report.id),
    )
    await db.commit()
    await db.refresh(report)
    return report


@router.post("/reports/{report_id}/submit", response_model=ReportOut)
async def mark_submitted(
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marked manually after the lawyer files the report with NjIF-K —
    the platform never sends anything automatically."""
    report = await db.get(SuspicionReport, report_id)
    if report is None or report.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    report.status = "submitted"
    report.submitted_at = datetime.now(UTC)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="aml.report_submit",
        entity_type="suspicion_report", entity_id=str(report.id),
    )
    await db.commit()
    await db.refresh(report)
    return report


_REPORT_PAGE = """<!DOCTYPE html>
<html lang="sq">
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: "DejaVu Sans", sans-serif; color: #1a2233; font-size: 12px; line-height: 1.5; }}
  .head {{ border-bottom: 3px solid #b91c1c; padding-bottom: 10px; margin-bottom: 22px; }}
  h1 {{ font-size: 16px; margin: 0 0 4px; }}
  .muted {{ color: #667; font-size: 10px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 14px 0; }}
  th, td {{ border: 1px solid #c8ccd6; padding: 7px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #fef2f2; width: 30%; font-weight: bold; }}
  .desc {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 14px; white-space: pre-line; }}
  .note {{ margin-top: 18px; font-size: 10.5px; color: #445; }}
  .foot {{ margin-top: 26px; border-top: 1px solid #d9dce3; padding-top: 8px; font-size: 9.5px; color: #778; }}
</style>
</head>
<body>
  <div class="head">
    <h1>RAPORT I BRENDSHËM I DYSHIMIT (AML)</h1>
    <div class="muted">Për dërgim te Njësia e Inteligjencës Financiare e Kosovës (NjIF-K) ·
    Ligji Nr. 05/L-096</div>
  </div>

  <table>
    <tr><th>Zyra ligjore</th><td>{firm}</td></tr>
    <tr><th>Zyrtari i përputhshmërisë</th><td>{officer}</td></tr>
    <tr><th>Përpiluar nga</th><td>{author}</td></tr>
    <tr><th>Data e përpilimit</th><td>{created}</td></tr>
    <tr><th>Lënda</th><td>{matter}</td></tr>
    <tr><th>Klienti / personi</th><td>{contact}</td></tr>
    <tr><th>Statusi</th><td>{status}</td></tr>
  </table>

  <h1 style="font-size:13px">Indikatorët e identifikuar</h1>
  <table>{indicator_rows}</table>

  <h1 style="font-size:13px">Përshkrimi i dyshimit</h1>
  <div class="desc">{description}</div>

  <div class="note"><b>Kujdes (neni 30):</b> ndalohet informimi i klientit ose
  palëve të treta se është përpiluar apo dërguar ky raport ("tipping-off").
  Raporti dërgohet te NjIF-K përmes kanaleve zyrtare të raportimit.</div>

  <div class="foot">Gjeneruar nga BoraLaw · {generated} · ID {report_id}</div>
</body>
</html>"""


@router.get("/reports/{report_id}/pdf")
async def report_pdf(
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from weasyprint import HTML

    report = await db.get(SuspicionReport, report_id)
    if report is None or report.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    tenant = await db.get(Tenant, user.tenant_id)
    officer = (
        await db.get(User, tenant.compliance_officer_id)
        if tenant.compliance_officer_id else None
    )
    author = await db.get(User, report.created_by_id) if report.created_by_id else None
    matter = await db.get(Matter, report.matter_id) if report.matter_id else None
    contact = await db.get(Contact, report.contact_id) if report.contact_id else None

    def esc(v: object) -> str:
        return html.escape(str(v)) if v not in (None, "") else "—"

    by_code = {i["code"]: i for i in XK_AML_INDICATORS}
    indicator_rows = "".join(
        f"<tr><th>{esc(code)}</th>"
        f"<td>{esc(by_code.get(code, {}).get('text', {}).get('sq', code))}</td></tr>"
        for code in (report.indicators or [])
    ) or "<tr><td>—</td></tr>"

    page = _REPORT_PAGE.format(
        firm=esc(tenant.name),
        officer=esc(officer.full_name if officer else None),
        author=esc(author.full_name if author else None),
        created=report.created_at.strftime("%d.%m.%Y %H:%M"),
        matter=esc(f"{matter.reference} — {matter.title}" if matter else None),
        contact=esc(contact.display_name if contact else None),
        status="I DËRGUAR" if report.status == "submitted" else "DRAFT",
        indicator_rows=indicator_rows,
        description=esc(report.description),
        generated=datetime.now(UTC).strftime("%d.%m.%Y %H:%M UTC"),
        report_id=str(report.id),
    )
    pdf = HTML(string=page).write_pdf()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="aml.report_pdf",
        entity_type="suspicion_report", entity_id=str(report.id),
    )
    await db.commit()
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="raport-dyshimi-{str(report.id)[:8]}.pdf"'
        },
    )
