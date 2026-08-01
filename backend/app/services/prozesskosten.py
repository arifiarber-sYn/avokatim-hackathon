"""German litigation cost-risk math (Prozesskostenrechner). Court fees per
§ 34 GKG / Anlage 2 and the per-instance lawyer fees are data in
`seeds/germany.py`; this module only computes.

The risk model follows § 91 ZPO (loser pays): for each instance the losing
party bears its own lawyer, the opponent's lawyer (statutory RVG amounts)
and the court fees. Lawyer fees carry VAT; court fees don't. Each instance
is its own Angelegenheit, so VV 7002 (20 %, max 20 €) applies per instance
and per lawyer.
"""
from decimal import ROUND_HALF_UP, Decimal

from app.seeds.germany import DE_GKG_TABLE, DE_PROZESSKOSTEN_INSTANCES

from app.services.rvg import banded_fee, base_fee

_CENT = Decimal("0.01")

INSTANCES_BY_CODE = {i["code"]: i for i in DE_PROZESSKOSTEN_INSTANCES}


def _round(x: Decimal) -> Decimal:
    return x.quantize(_CENT, rounding=ROUND_HALF_UP)


def court_fee_unit(value: Decimal) -> Decimal:
    """The 1.0 court fee for a Streitwert per § 34 GKG / Anlage 2."""
    return banded_fee(value, DE_GKG_TABLE)


def _lawyer_cost(fee1: Decimal, instance: dict, vat_rate: int) -> dict:
    """Statutory cost of one lawyer in one instance: fee lines + VV 7002
    expense flat + VAT."""
    minimum = Decimal("15.00")  # § 13 Abs. 2 RVG
    lines = []
    fees = Decimal(0)
    for item in instance["lawyer_items"]:
        amount = max(_round(fee1 * Decimal(item["rate"])), minimum)
        fees += amount
        lines.append(
            {
                "vv": item["vv"],
                "rate": item["rate"],
                "name": item["name"],
                "amount": str(amount),
            }
        )
    pauschale = min(_round(fees * Decimal("0.20")), Decimal("20.00"))
    lines.append(
        {
            "vv": "VV 7002",
            "rate": None,
            "name": {
                "de": "Post- und Telekommunikationspauschale",
                "en": "Post/telecom flat expense",
                "sq": "Paushalli postar/telekomunikimi",
            },
            "amount": str(pauschale),
        }
    )
    net = fees + pauschale
    vat = _round(net * Decimal(vat_rate) / 100)
    return {"lines": lines, "net": str(net), "vat": str(vat), "total": str(_round(net + vat))}


def cost_risk(
    value: Decimal,
    instance_codes: list[str] | None = None,
    vat_rate: int = 19,
) -> dict:
    """Cost risk per instance and cumulative, § 91 ZPO model.

    Per instance: own lawyer (RVG + VAT), opponent's lawyer (same statutory
    amounts) and the court fee (GKG rate x unit fee, no VAT). `total_if_lose`
    = all three; `total_if_win` = 0 for that instance (the opponent bears
    everything under § 91 ZPO — informative simplification)."""
    codes = instance_codes or [i["code"] for i in DE_PROZESSKOSTEN_INSTANCES]
    fee1 = base_fee(value)
    unit = court_fee_unit(value)

    instances = []
    cumulative = Decimal(0)
    for code in codes:
        inst = INSTANCES_BY_CODE.get(code)
        if inst is None:
            continue
        lawyer = _lawyer_cost(fee1, inst, vat_rate)
        court = _round(unit * Decimal(inst["court_rate"]))
        lose = Decimal(lawyer["total"]) * 2 + court
        cumulative += lose
        instances.append(
            {
                "code": inst["code"],
                "name": inst["name"],
                "court_kv": inst["court_kv"],
                "court_rate": inst["court_rate"],
                "court_fee": str(court),
                "own_lawyer": lawyer,
                "opponent_lawyer_total": lawyer["total"],
                "total_if_lose": str(_round(lose)),
                "cumulative_if_lose": str(_round(cumulative)),
            }
        )

    return {
        "value": str(value),
        "rvg_base_fee": str(fee1),
        "gkg_unit_fee": str(unit),
        "vat_rate": vat_rate,
        "legal_basis": (
            f"{DE_GKG_TABLE['legal_basis']}; § 13 RVG (KostBRÄG 2025); § 91 ZPO"
        ),
        "court_fee_advance": str(_round(unit * Decimal("3.0"))),  # § 12 GKG
        "instances": instances,
        "total_risk": str(_round(cumulative)),
    }
