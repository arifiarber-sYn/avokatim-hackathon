"""Public tools for citizens (no account needed): the deadline calculator
over the existing deadline engine, simple document generation from
deterministic templates, and the notary helper (directory + fee estimate).
Jurisdiction rules and templates stay data-driven."""
import html
import json
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jinja2 import Template
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.marketplace import _ip, _rate_limit
from app.config import PROJECT_DIR
from app.database import get_db
from app.jurisdictions import country_from_request
from app.models import DeadlineRule, Jurisdiction
from app.seeds.citizen_docs import CITIZEN_DOC_TEMPLATES
from app.seeds.notary import (
    NOTARY_ACTS,
    NOTARY_CHECKLIST_LABELS,
    SOLEMNIZATION_FACTOR,
    annex1_fee,
)
from app.services.deadlines import compute_due_date

router = APIRouter(prefix="/public/tools", tags=["public-tools"])


@router.get("/deadline-rules")
async def public_deadline_rules(request: Request, db: AsyncSession = Depends(get_db)):
    """Rules of the requesting host's country, for the public calculator."""
    stmt = (
        select(DeadlineRule, Jurisdiction.code)
        .join(Jurisdiction, Jurisdiction.id == DeadlineRule.jurisdiction_id)
        .where(
            Jurisdiction.is_active.is_(True),
            Jurisdiction.code == country_from_request(request),
        )
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


# ---------- notary helper ----------

NOTARIES_FILE = PROJECT_DIR / "data" / "notaries.json"
_notaries_cache: dict = {"mtime": None, "data": None}


def _load_notaries() -> dict:
    """Directory scraped from the public ONK registry (scrape_onk_registry.py);
    cached in memory and reloaded when the file changes."""
    try:
        mtime = NOTARIES_FILE.stat().st_mtime
    except FileNotFoundError:
        return {"notaries": [], "fetched_at": None}
    if _notaries_cache["mtime"] != mtime:
        _notaries_cache["data"] = json.loads(NOTARIES_FILE.read_text(encoding="utf-8"))
        _notaries_cache["mtime"] = mtime
    return _notaries_cache["data"]


def _norm(name: str) -> str:
    return " ".join(name.lower().replace("ë", "e").replace("ç", "c").split())


async def _registered_notaries(db: AsyncSession) -> list[dict]:
    """Verified notary offices registered on the platform. They appear in the
    directory like everyone else (equal listing — no promoted placement),
    but with a verification badge and, when enabled, an online booking button."""
    from app.models import LawyerProfile, Tenant, User

    rows = (
        await db.execute(
            select(LawyerProfile, User, Tenant)
            .join(User, User.id == LawyerProfile.user_id)
            .join(Tenant, Tenant.id == LawyerProfile.tenant_id)
            .where(
                Tenant.profession == "notary",
                Tenant.status == "active",
                LawyerProfile.is_visible.is_(True),
                LawyerProfile.verification_status == "verified",
                User.is_active.is_(True),
            )
            .order_by(LawyerProfile.created_at)
        )
    ).all()
    return [
        {
            "name": user.full_name,
            "phone": profile.phone or "",
            "email": user.email,
            "address": tenant.address or "",
            "city": (profile.cities or [""])[0],
            "registered": True,
            "profile_id": str(profile.id),
            "booking": bool(profile.booking_enabled),
            "bio": profile.bio,
        }
        for profile, user, tenant in rows
    ]


@router.get("/notaries")
async def public_notaries(city: str | None = None, db: AsyncSession = Depends(get_db)):
    data = _load_notaries()
    registered = await _registered_notaries(db)
    # Registered offices replace their scraped registry entry (name match)
    registered_names = {_norm(n["name"]) for n in registered}
    scraped = [
        n for n in data.get("notaries", [])
        if _norm(n.get("name", "")) not in registered_names
    ]
    notaries = registered + scraped
    if city:
        needle = city.strip().lower()
        notaries = [n for n in notaries if needle in n.get("city", "").lower()]
    cities = sorted({n["city"] for n in (registered + scraped) if n.get("city")})
    return {
        "notaries": notaries,
        "cities": cities,
        "total": len(registered) + len(scraped),
        "source": data.get("source"),
        "fetched_at": data.get("fetched_at"),
    }


@router.get("/notary-acts")
async def notary_acts():
    """Common notarial matters: act type, document checklist, fee model."""
    return {
        "acts": [
            {
                "code": a["code"],
                "act_type": a["act_type"],
                "value_based": a["value_based"],
                "per_unit": a.get("per_unit"),
                "mandatory_solemnization": a.get("mandatory_solemnization", False),
                "name": a["name"],
                "checklist": [
                    {"key": k, "label": NOTARY_CHECKLIST_LABELS[k]}
                    for k in a["checklist"]
                ],
            }
            for a in NOTARY_ACTS
        ],
    }


class NotaryFeeIn(BaseModel):
    act_code: str
    value_eur: float | None = Field(default=None, ge=0, le=100_000_000)
    units: int = Field(default=1, ge=1, le=500)


@router.post("/notary-fee")
async def notary_fee_estimate(body: NotaryFeeIn, request: Request):
    """Estimate per AI 02/2012: Annex 1 brackets, 80% for solemnization of
    party-drafted documents (art. 23), fixed fees otherwise. Informative only."""
    await _rate_limit("public_notary_fee", _ip(request), limit=60, window_seconds=3600)
    act = next((a for a in NOTARY_ACTS if a["code"] == body.act_code), None)
    if act is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown act")
    if act["value_based"]:
        if body.value_eur is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "value_eur required")
        base = annex1_fee(body.value_eur)
        fee = round(base * SOLEMNIZATION_FACTOR) if act["fee"] == "solemnizim" else base
    else:
        fee = act["fee"]["fixed"] * (body.units if act.get("per_unit") else 1)
    return {
        "act_code": act["code"],
        "act_type": act["act_type"],
        "fee_eur": fee,
        "legal_basis": "UA nr. 02/2012 për tarifat e përkohshme noteriale",
        "estimate": True,
    }


# ---------- simple citizen documents ----------

@router.get("/documents")
async def citizen_doc_templates():
    """Available self-service templates with their plain-language fields."""
    return [
        {
            "code": tpl["code"],
            "category": tpl["category"],
            "name": tpl["name"],
            "fields": tpl["fields"],
            "requires_notary": tpl.get("requires_notary", False),
            "notary_act": tpl.get("notary_act"),
        }
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
