"""Public tools for citizens (no account needed): the deadline calculator
over the existing deadline engine, and simple document generation from
deterministic templates. Jurisdiction rules and templates stay data-driven."""
import html
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jinja2 import Template
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.marketplace import _ip, _rate_limit
from app.database import get_db
from app.models import DeadlineRule, Jurisdiction
from app.seeds.citizen_docs import CITIZEN_DOC_TEMPLATES
from app.services.deadlines import compute_due_date

router = APIRouter(prefix="/public/tools", tags=["public-tools"])


@router.get("/deadline-rules")
async def public_deadline_rules(db: AsyncSession = Depends(get_db)):
    """Active-jurisdiction rules with localized names, for the public calculator."""
    stmt = (
        select(DeadlineRule, Jurisdiction.code)
        .join(Jurisdiction, Jurisdiction.id == DeadlineRule.jurisdiction_id)
        .where(Jurisdiction.is_active.is_(True))
        .order_by(DeadlineRule.practice_area, DeadlineRule.code)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": str(rule.id),
            "jurisdiction": code,
            "code": rule.code,
            "name": rule.name,
            "legal_basis": rule.legal_basis,
            "practice_area": rule.practice_area,
            "trigger_event": rule.trigger_event,
            "days": rule.days,
            "day_type": rule.day_type,
        }
        for rule, code in rows
    ]


class CalcIn(BaseModel):
    rule_id: uuid.UUID
    trigger_date: date


@router.post("/deadline-calc")
async def public_deadline_calc(
    body: CalcIn, request: Request, db: AsyncSession = Depends(get_db)
):
    await _rate_limit("public_deadline_calc", _ip(request), limit=60, window_seconds=3600)
    rule = await db.get(DeadlineRule, body.rule_id)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found")
    due = await compute_due_date(db, rule, body.trigger_date)
    return {
        "due_date": due.isoformat(),
        "days": rule.days,
        "day_type": rule.day_type,
        "legal_basis": rule.legal_basis,
        "name": rule.name,
    }


# ---------- simple citizen documents ----------

@router.get("/documents")
async def citizen_doc_templates():
    """Available self-service templates with their plain-language fields."""
    return [
        {"code": tpl["code"], "name": tpl["name"], "fields": tpl["fields"]}
        for tpl in CITIZEN_DOC_TEMPLATES
    ]


class DocIn(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)


@router.post("/documents/{code}")
async def citizen_generate_document(
    code: str, body: DocIn, request: Request
) -> Response:
    """Deterministic render (no LLM): fill the template, return a PDF."""
    await _rate_limit("public_citizen_doc", _ip(request), limit=20, window_seconds=3600)
    tpl = next((t for t in CITIZEN_DOC_TEMPLATES if t["code"] == code), None)
    if tpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    values: dict[str, str] = {}
    for field in tpl["fields"]:
        value = (body.values.get(field["key"]) or "").strip()
        if not value:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"Missing field: {field['key']}"
            )
        values[field["key"]] = value[:4000]
    values["date"] = datetime.now().strftime("%d.%m.%Y")
    text = Template(tpl["body_sq"]).render(**values)

    from weasyprint import HTML

    doc_html = f"""<html><head><meta charset="utf-8"><style>
      @page {{ size: A4; margin: 2.5cm; }}
      body {{ font-family: serif; font-size: 12pt; color: #111; }}
      pre {{ white-space: pre-wrap; font-family: inherit; line-height: 1.6; }}
      footer {{ font-size: 8pt; color: #999; margin-top: 2em; }}
    </style></head><body>
      <pre>{html.escape(text)}</pre>
      <footer>Gjeneruar me AvokatIM ({datetime.now().strftime("%d.%m.%Y %H:%M")}) —
      dokument informues, rishikoje para dorëzimit.</footer>
    </body></html>"""
    pdf = HTML(string=doc_html).write_pdf()
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{code}-avokatim.pdf"'},
    )
