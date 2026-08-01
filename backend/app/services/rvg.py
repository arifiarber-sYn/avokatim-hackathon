"""German statutory lawyer-fee math (RVG). The § 13 table and the VV item
catalogue are data in `seeds/germany.py`; this module only computes.

A calculation returns individual fee lines so they can be shown to a citizen
(public Prozesskosten estimate) or inserted 1:1 as invoice items by a lawyer.
Rules implemented:
- § 13 Abs. 1 RVG banded value table (KostBRÄG 2025), § 13 Abs. 2 minimum.
- Fee = 1.0 fee x VV rate, kaufmännisch rounded (ROUND_HALF_UP, 2 places).
- Anrechnung Vorbem. 3 Abs. 4 VV: half the Geschäftsgebühr rate (max 0.75)
  is credited against the Verfahrensgebühr when both are selected.
- VV 7002 Auslagenpauschale: 20 % of the fees, max 20 € — per Angelegenheit
  (the out-of-court and the court matter each get their own).
"""
from decimal import ROUND_HALF_UP, Decimal

from app.seeds.germany import DE_RVG_TABLE, DE_RVG_VV_ITEMS

_CENT = Decimal("0.01")

VV_ITEMS_BY_CODE = {item["code"]: item for item in DE_RVG_VV_ITEMS}


def _round(x: Decimal) -> Decimal:
    return x.quantize(_CENT, rounding=ROUND_HALF_UP)


def base_fee(value: Decimal) -> Decimal:
    """The 1.0 fee for a Gegenstandswert per § 13 Abs. 1 RVG."""
    if value <= 0:
        return Decimal(DE_RVG_TABLE["minimum_fee"])
    fee = Decimal(DE_RVG_TABLE["base_fee"])
    reached = Decimal(DE_RVG_TABLE["base_up_to"])
    for step_s, ceiling_s, increment_s in DE_RVG_TABLE["bands"]:
        step, increment = Decimal(step_s), Decimal(increment_s)
        ceiling = Decimal(ceiling_s) if ceiling_s else None
        while value > reached and (ceiling is None or reached < ceiling):
            fee += increment  # per *started* step
            reached += step
        if value <= reached:
            break
    return max(fee, Decimal(DE_RVG_TABLE["minimum_fee"]))


def compute(
    value: Decimal,
    item_codes: list[str],
    geschaeftsgebuehr_rate: Decimal | None = None,
    vat_rate: int = 19,
) -> dict:
    """Fee lines + totals for the selected VV items at a Gegenstandswert."""
    fee1 = base_fee(value)
    lines: list[dict] = []
    group_fees: dict[str, Decimal] = {}

    selected = [VV_ITEMS_BY_CODE[c] for c in item_codes if c in VV_ITEMS_BY_CODE]
    minimum = Decimal(DE_RVG_TABLE["minimum_fee"])

    gg_rate: Decimal | None = None
    for item in selected:
        rate = Decimal(item["rate"])
        if item["code"] == "geschaeftsgebuehr" and geschaeftsgebuehr_rate:
            rate = max(
                Decimal(item["rate_min"]),
                min(Decimal(item["rate_max"]), geschaeftsgebuehr_rate),
            )
        if item["code"] == "geschaeftsgebuehr":
            gg_rate = rate
        amount = max(_round(fee1 * rate), minimum)
        lines.append(
            {
                "code": item["code"],
                "vv": item["vv"],
                "name": item["name"],
                "rate": str(rate),
                "amount": str(amount),
            }
        )
        group_fees[item["group"]] = group_fees.get(item["group"], Decimal(0)) + amount

    codes = {i["code"] for i in selected}
    if gg_rate is not None and "verfahrensgebuehr" in codes:
        credit_rate = min(gg_rate / 2, Decimal("0.75"))
        credit = -_round(fee1 * credit_rate)
        lines.append(
            {
                "code": "anrechnung",
                "vv": "Vorbem. 3 Abs. 4 VV",
                "name": {
                    "de": "Anrechnung der Geschäftsgebühr",
                    "en": "Credit of the business fee",
                    "sq": "Zbritja e tarifës jashtëgjyqësore",
                },
                "rate": str(credit_rate),
                "amount": str(credit),
            }
        )
        group_fees["gerichtlich"] = group_fees.get("gerichtlich", Decimal(0)) + credit

    for group, label in (
        ("aussergerichtlich", "außergerichtlich"),
        ("gerichtlich", "gerichtlich"),
    ):
        fees = group_fees.get(group)
        if fees and fees > 0:
            pauschale = min(_round(fees * Decimal("0.20")), Decimal("20.00"))
            lines.append(
                {
                    "code": f"auslagen_{group}",
                    "vv": "VV 7002",
                    "name": {
                        "de": f"Post- und Telekommunikationspauschale ({label})",
                        "en": f"Post/telecom flat expense ({label})",
                        "sq": f"Paushalli postar/telekomunikimi ({label})",
                    },
                    "rate": None,
                    "amount": str(pauschale),
                }
            )

    net = sum(Decimal(line["amount"]) for line in lines)
    vat = _round(net * Decimal(vat_rate) / 100)
    return {
        "value": str(value),
        "base_fee": str(fee1),
        "legal_basis": DE_RVG_TABLE["legal_basis"],
        "lines": lines,
        "net": str(_round(net)),
        "vat_rate": vat_rate,
        "vat": str(vat),
        "total": str(_round(net + vat)),
    }
