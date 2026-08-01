"""Idempotent seeding of jurisdiction data (runs at startup).

One generic country seeder (D-034): jurisdiction row, deadline rules,
holidays, global document templates and the fee tariff — all data-driven.
Kosovo (XK) and Germany (DE) are seeded; adding a country = adding a data
module, never service code.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeadlineRule, DocumentTemplate, FeeTariffItem, Holiday, Jurisdiction
from app.seeds.germany import (
    DE_DEADLINE_RULES,
    DE_FEE_TARIFF,
    DE_JURISDICTION,
    DE_TEMPLATES,
    de_holidays,
)
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


def _xk_holidays(year: int) -> list[tuple[date, dict]]:
    out = []
    for mmdd, name in XK_HOLIDAYS_FIXED:
        month, day = (int(x) for x in mmdd.split("-"))
        out.append((date(year, month, day), name))
    return out


async def _seed_country(
    db: AsyncSession,
    code: str,
    rules: list[dict],
    holidays_for_year,
    templates: list[dict],
    tariff: list[dict],
) -> None:
    jurisdiction = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == code))
    ).scalar_one()

    existing_rules = {
        r.code: r
        for r in (
            await db.execute(
                select(DeadlineRule).where(DeadlineRule.jurisdiction_id == jurisdiction.id)
            )
        ).scalars()
    }
    for rule in rules:
        if rule["code"] not in existing_rules:
            db.add(DeadlineRule(jurisdiction_id=jurisdiction.id, **rule))
        else:
            merged = _merge_name(existing_rules[rule["code"]].name, rule["name"])
            if merged:
                existing_rules[rule["code"]].name = merged

    existing_holidays = {
        h.day: h
        for h in (
            await db.execute(
                select(Holiday).where(Holiday.jurisdiction_id == jurisdiction.id)
            )
        ).scalars()
    }
    this_year = date.today().year
    for year in (this_year, this_year + 1):
        for d, name in holidays_for_year(year):
            if d not in existing_holidays:
                db.add(Holiday(jurisdiction_id=jurisdiction.id, day=d, name=name))
            else:
                merged = _merge_name(existing_holidays[d].name, name)
                if merged:
                    existing_holidays[d].name = merged

    existing_templates = {
        (t.code, t.locale)
        for t in (
            await db.execute(
                select(DocumentTemplate).where(
                    DocumentTemplate.jurisdiction_id == jurisdiction.id,
                    DocumentTemplate.tenant_id.is_(None),
                )
            )
        ).scalars()
    }
    for tpl in templates:
        if (tpl["code"], tpl["locale"]) not in existing_templates:
            db.add(DocumentTemplate(jurisdiction_id=jurisdiction.id, tenant_id=None, **tpl))

    existing_tariff = {
        t.code: t
        for t in (
            await db.execute(
                select(FeeTariffItem).where(FeeTariffItem.jurisdiction_id == jurisdiction.id)
            )
        ).scalars()
    }
    for item in tariff:
        if item["code"] not in existing_tariff:
            db.add(FeeTariffItem(jurisdiction_id=jurisdiction.id, **item))
        else:
            merged = _merge_name(existing_tariff[item["code"]].name, item["name"])
            if merged:
                existing_tariff[item["code"]].name = merged


async def seed_jurisdictions(db: AsyncSession) -> None:
    for j in [*JURISDICTIONS, DE_JURISDICTION]:
        existing = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == j["code"]))
        ).scalar_one_or_none()
        if existing is None:
            db.add(Jurisdiction(**j))
        else:
            merged = _merge_name(existing.name, j["name"])
            if merged:
                existing.name = merged
            if j.get("is_active") and not existing.is_active:
                existing.is_active = True
    await db.flush()

    await _seed_country(
        db, "XK", XK_DEADLINE_RULES, _xk_holidays, XK_TEMPLATES, XK_FEE_TARIFF
    )
    await _seed_country(
        db, "DE", DE_DEADLINE_RULES, de_holidays, DE_TEMPLATES, DE_FEE_TARIFF
    )

    await db.commit()
