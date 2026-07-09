"""Idempotent seeding of jurisdiction data (runs at startup)."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeadlineRule, DocumentTemplate, FeeTariffItem, Holiday, Jurisdiction
from app.seeds.kosovo import (
    JURISDICTIONS,
    XK_DEADLINE_RULES,
    XK_FEE_TARIFF,
    XK_HOLIDAYS_FIXED,
    XK_TEMPLATES,
)


async def seed_jurisdictions(db: AsyncSession) -> None:
    for j in JURISDICTIONS:
        existing = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == j["code"]))
        ).scalar_one_or_none()
        if existing is None:
            db.add(Jurisdiction(**j))
    await db.flush()

    xk = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == "XK"))
    ).scalar_one()

    existing_rules = {
        r.code
        for r in (
            await db.execute(select(DeadlineRule).where(DeadlineRule.jurisdiction_id == xk.id))
        ).scalars()
    }
    for rule in XK_DEADLINE_RULES:
        if rule["code"] not in existing_rules:
            db.add(DeadlineRule(jurisdiction_id=xk.id, **rule))

    existing_holidays = {
        h.day
        for h in (
            await db.execute(select(Holiday).where(Holiday.jurisdiction_id == xk.id))
        ).scalars()
    }
    this_year = date.today().year
    for year in (this_year, this_year + 1):
        for mmdd, name in XK_HOLIDAYS_FIXED:
            month, day = (int(x) for x in mmdd.split("-"))
            d = date(year, month, day)
            if d not in existing_holidays:
                db.add(Holiday(jurisdiction_id=xk.id, day=d, name=name))

    existing_templates = {
        (t.code, t.locale)
        for t in (
            await db.execute(
                select(DocumentTemplate).where(
                    DocumentTemplate.jurisdiction_id == xk.id,
                    DocumentTemplate.tenant_id.is_(None),
                )
            )
        ).scalars()
    }
    for tpl in XK_TEMPLATES:
        if (tpl["code"], tpl["locale"]) not in existing_templates:
            db.add(DocumentTemplate(jurisdiction_id=xk.id, tenant_id=None, **tpl))

    existing_tariff = {
        t.code
        for t in (
            await db.execute(
                select(FeeTariffItem).where(FeeTariffItem.jurisdiction_id == xk.id)
            )
        ).scalars()
    }
    for item in XK_FEE_TARIFF:
        if item["code"] not in existing_tariff:
            db.add(FeeTariffItem(jurisdiction_id=xk.id, **item))

    await db.commit()
