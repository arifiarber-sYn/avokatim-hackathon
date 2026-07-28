"""Office-level Ava: answers questions about the firm's own data.

Fixed, auditable pipeline (the D-030 principle — no free-form tool loop):

1. The LLM classifies the question into ONE of ~8 predefined tools.
2. The tool runs a hand-written, tenant-scoped SQLAlchemy query — the LLM
   never writes SQL and never sees data outside the tenant.
3. The LLM phrases the answer in the UI language using the real numbers.

Every tool returns plain dict rows so step 3 receives exactly what the
lawyer could also read in reports — nothing more.
"""
import json
import logging
import re
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm import get_provider
from app.llm.base import ChatMessage
from app.models import (
    CaseRequest,
    ConsultBooking,
    Contact,
    Deadline,
    IntakeRequest,
    Invoice,
    Matter,
    TimeEntry,
    User,
)

logger = logging.getLogger(__name__)


def _dec(value: Decimal | None) -> float:
    return float(value or 0)


async def _unpaid_invoices(db: AsyncSession, tenant_id: uuid.UUID) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.tenant_id == tenant_id, Invoice.status == "sent")
    )
    return list((await db.execute(stmt)).scalars())


async def tool_debts_by_client(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Unpaid (sent) invoice totals grouped by client."""
    invoices = await _unpaid_invoices(db, tenant_id)
    totals: dict[uuid.UUID | None, Decimal] = {}
    for inv in invoices:
        totals[inv.contact_id] = totals.get(inv.contact_id, Decimal("0")) + inv.total_with_vat
    rows = []
    for contact_id, total in totals.items():
        name = "—"
        if contact_id:
            contact = await db.get(Contact, contact_id)
            name = contact.display_name if contact else "—"
        rows.append({"client": name, "unpaid_eur": _dec(total)})
    return sorted(rows, key=lambda r: -r["unpaid_eur"])[:20]


async def tool_week_deadlines(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Deadlines due in the next 7 days."""
    now = datetime.now(UTC)
    stmt = (
        select(Deadline, Matter.reference, Matter.title)
        .join(Matter, Matter.id == Deadline.matter_id)
        .where(
            Deadline.tenant_id == tenant_id,
            Deadline.status == "pending",
            Deadline.due_at >= now,
            Deadline.due_at <= now + timedelta(days=7),
        )
        .order_by(Deadline.due_at)
        .limit(30)
    )
    return [
        {
            "due_at": d.due_at.isoformat(),
            "kind": d.kind,
            "title": d.title,
            "matter": f"{ref} — {title}",
        }
        for d, ref, title in (await db.execute(stmt)).all()
    ]


async def tool_stale_matters(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Open matters with no changes for 30+ days."""
    cutoff = datetime.now(UTC) - timedelta(days=30)
    stmt = (
        select(Matter)
        .where(
            Matter.tenant_id == tenant_id,
            Matter.status == "open",
            Matter.updated_at < cutoff,
        )
        .order_by(Matter.updated_at)
        .limit(30)
    )
    return [
        {
            "reference": m.reference,
            "title": m.title,
            "last_activity": m.updated_at.date().isoformat(),
        }
        for m in (await db.execute(stmt)).scalars()
    ]


async def tool_hours_by_user(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Recorded hours per person this month."""
    month_start = date.today().replace(day=1)
    stmt = (
        select(User.full_name, func.sum(TimeEntry.minutes))
        .join(User, User.id == TimeEntry.user_id)
        .where(TimeEntry.tenant_id == tenant_id, TimeEntry.started_at >= month_start)
        .group_by(User.full_name)
    )
    return [
        {"user": name, "hours": round((minutes or 0) / 60, 1)}
        for name, minutes in (await db.execute(stmt)).all()
    ]


async def tool_revenue_by_area(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Paid invoice totals per practice area this year."""
    year_start = date.today().replace(month=1, day=1)
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.status == "paid",
            Invoice.paid_on >= year_start,
        )
    )
    totals: dict[str, Decimal] = {}
    for inv in (await db.execute(stmt)).scalars():
        area = "other"
        if inv.matter_id:
            matter = await db.get(Matter, inv.matter_id)
            area = matter.practice_area if matter else "other"
        totals[area] = totals.get(area, Decimal("0")) + inv.total_with_vat
    return [
        {"practice_area": a, "revenue_eur": _dec(v)}
        for a, v in sorted(totals.items(), key=lambda kv: -kv[1])
    ]


async def tool_ar_aging(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Unpaid invoices bucketed by how overdue they are."""
    today = date.today()
    buckets = {"0_30": Decimal("0"), "31_60": Decimal("0"), "61_90": Decimal("0"), "91_plus": Decimal("0")}
    for inv in await _unpaid_invoices(db, tenant_id):
        anchor = inv.due_on or inv.issued_on or today
        days = (today - anchor).days
        if days <= 30:
            key = "0_30"
        elif days <= 60:
            key = "31_60"
        elif days <= 90:
            key = "61_90"
        else:
            key = "91_plus"
        buckets[key] += inv.total_with_vat
    return [{"bucket": k, "unpaid_eur": _dec(v)} for k, v in buckets.items()]


async def tool_upcoming_bookings(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Confirmed/pending consultations coming up."""
    stmt = (
        select(ConsultBooking)
        .where(
            ConsultBooking.tenant_id == tenant_id,
            ConsultBooking.status.in_(["pending", "confirmed"]),
            ConsultBooking.starts_at >= datetime.now(UTC),
        )
        .order_by(ConsultBooking.starts_at)
        .limit(20)
    )
    return [
        {
            "starts_at": b.starts_at.isoformat(),
            "duration_min": b.duration_min,
            "status": b.status,
            "fee_eur": b.fee_eur,
        }
        for b in (await db.execute(stmt)).scalars()
    ]


async def tool_intake_stats(db: AsyncSession, tenant_id: uuid.UUID) -> list[dict]:
    """Pipeline counts: intake requests by status + marketplace cases claimed."""
    intake_rows = (
        await db.execute(
            select(IntakeRequest.status, func.count())
            .where(IntakeRequest.tenant_id == tenant_id)
            .group_by(IntakeRequest.status)
        )
    ).all()
    claimed = (
        await db.execute(
            select(func.count()).where(CaseRequest.claimed_by_tenant_id == tenant_id)
        )
    ).scalar_one()
    rows = [{"metric": f"intake_{s}", "count": c} for s, c in intake_rows]
    rows.append({"metric": "marketplace_cases_claimed", "count": claimed})
    return rows


OFFICE_TOOLS = {
    "debts_by_client": {
        "run": tool_debts_by_client,
        "description": "Borxhet e klientëve: faturat e dërguara e të papaguara, të grupuara sipas klientit",
    },
    "week_deadlines": {
        "run": tool_week_deadlines,
        "description": "Afatet e 7 ditëve të ardhshme me lëndët përkatëse",
    },
    "stale_matters": {
        "run": tool_stale_matters,
        "description": "Lëndët e hapura pa asnjë aktivitet për 30+ ditë",
    },
    "hours_by_user": {
        "run": tool_hours_by_user,
        "description": "Orët e regjistruara këtë muaj sipas personit",
    },
    "revenue_by_area": {
        "run": tool_revenue_by_area,
        "description": "Të hyrat e paguara këtë vit sipas fushës së praktikës",
    },
    "ar_aging": {
        "run": tool_ar_aging,
        "description": "Vjetërsia e faturave të papaguara (0-30, 31-60, 61-90, 91+ ditë)",
    },
    "upcoming_bookings": {
        "run": tool_upcoming_bookings,
        "description": "Konsultat e ardhshme të rezervuara nga qytetarët",
    },
    "intake_stats": {
        "run": tool_intake_stats,
        "description": "Statistikat e pranimit: kërkesat intake sipas statusit dhe rastet e marra nga tregu",
    },
}

_CLASSIFY_PROMPT = """Ti klasifikon pyetje për të dhënat e një zyre ligjore.
Zgjidh SAKTËSISHT një vegël nga lista (ose "none" nëse asnjëra nuk përshtatet):

{tools}

Kthe VETËM JSON: {{"tool": "<id ose none>"}}

Pyetja: {question}"""

_ANSWER_PROMPT = """Pyetja e avokatit: {question}

Të dhënat reale nga sistemi (vegla '{tool}'):
{data}

Përgjigju shkurt e qartë në gjuhën me kod '{language}', duke përdorur VETËM
shifrat e mësipërme. Formato shumat si EUR. Nëse lista është bosh, thuaje."""


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


async def classify_office_question(
    question: str, provider_name: str | None = None
) -> str | None:
    """Step 1: map the question to a tool id, or None."""
    tools_text = "\n".join(
        f"- {tool_id}: {spec['description']}" for tool_id, spec in OFFICE_TOOLS.items()
    )
    provider = get_provider(provider_name)
    result = await provider.chat(
        [
            ChatMessage(
                role="user",
                content=_CLASSIFY_PROMPT.format(tools=tools_text, question=question[:2000]),
            )
        ]
    )
    parsed = _extract_json(result.content)
    tool = (parsed or {}).get("tool")
    return tool if tool in OFFICE_TOOLS else None


async def office_ask(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    question: str,
    language: str = "sq",
    provider_name: str | None = None,
) -> dict:
    """The full pipeline. Returns {answer, tool, data}."""
    tool_id = await classify_office_question(question, provider_name)
    if tool_id is None:
        return {"answer": None, "tool": None, "data": []}
    rows = await OFFICE_TOOLS[tool_id]["run"](db, tenant_id)
    provider = get_provider(provider_name)
    result = await provider.chat(
        [
            ChatMessage(
                role="user",
                content=_ANSWER_PROMPT.format(
                    question=question[:2000],
                    tool=tool_id,
                    data=json.dumps(rows, ensure_ascii=False, default=str)[:8000],
                    language=language,
                ),
            )
        ]
    )
    return {"answer": result.content, "tool": tool_id, "data": rows}
