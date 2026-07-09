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


def _merge_name(existing_name: dict | None, seed_name: dict) -> dict | None:
    """Add locales the seed gained (e.g. sr/tr/bs, Law 02/L-37) to an existing
    row's name without overwriting values the lawyer may have edited.
    Returns the merged dict, or None when nothing changed."""
    current = dict(existing_name or {})
    merged = {**seed_name, **current}
    return merged if merged != current else None


async def seed_jurisdictions(db: AsyncSession) -> None:
    for j in JURISDICTIONS:
        existing = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == j["code"]))
        ).scalar_one_or_none()
        if existing is None:
            db.add(Jurisdiction(**j))
        else:
            merged = _merge_name(existing.name, j["name"])
            if merged:
                existing.name = merged
    await db.flush()

    xk = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == "XK"))
    ).scalar_one()

    existing_rules = {
        r.code: r
        for r in (
            await db.execute(select(DeadlineRule).where(DeadlineRule.jurisdiction_id == xk.id))
        ).scalars()
    }
    for rule in XK_DEADLINE_RULES:
        if rule["code"] not in existing_rules:
            db.add(DeadlineRule(jurisdiction_id=xk.id, **rule))
        else:
            merged = _merge_name(existing_rules[rule["code"]].name, rule["name"])
            if merged:
                existing_rules[rule["code"]].name = merged

    existing_holidays = {
        h.day: h
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
            else:
                merged = _merge_name(existing_holidays[d].name, name)
                if merged:
                    existing_holidays[d].name = merged

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
        t.code: t
        for t in (
            await db.execute(
                select(FeeTariffItem).where(FeeTariffItem.jurisdiction_id == xk.id)
            )
        ).scalars()
    }
    for item in XK_FEE_TARIFF:
        if item["code"] not in existing_tariff:
            db.add(FeeTariffItem(jurisdiction_id=xk.id, **item))
        else:
            merged = _merge_name(existing_tariff[item["code"]].name, item["name"])
            if merged:
                existing_tariff[item["code"]].name = merged

    await db.commit()
