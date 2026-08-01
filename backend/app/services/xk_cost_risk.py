"""Kosovo litigation cost-risk math — the XK twin of prozesskosten.py.

Court fees come from XK_COURT_FEE_TABLE (UA Nr. 03/2025 of the KGJK, data
not code); lawyer fees follow the OAK tariff (one submission per instance,
nr. tarifor 6, plus hearings, nr. tarifor 7, plus the 30% paushall). The
risk model is loser-pays per nenet 449 dhe 452 të LPK-së: the losing party
bears its own lawyer, the opponent's lawyer and the court fee.
"""
from decimal import ROUND_HALF_UP, Decimal

from app.seeds.kosovo import XK_COST_RISK_INSTANCES, XK_COURT_FEE_TABLE

_CENT = Decimal("0.01")

INSTANCES_BY_CODE = {i["code"]: i for i in XK_COST_RISK_INSTANCES}

# OAK tariff bands for civil submissions/hearings (nr. tarifor 6 dhe 7):
# small-value dispute (deri 3.000 €, neni 468 i LPK-së), up to 10.000 €,
# over 10.000 € — the same amount applies per submission and per hearing.
_OAK_BANDS = [
    (Decimal("3000"), Decimal("60.00")),
    (Decimal("10000"), Decimal("80.00")),
]
_OAK_TOP = Decimal("160.00")
_PAUSHALL = Decimal("0.30")  # 30% flat add-on of the OAK tariff

_HEARING_LABEL = {
    "sq": "Përfaqësimi në seanca (nr. tarifor 7)",
    "en": "Hearing representation (tariff no. 7)",
    "de": "Terminswahrnehmung (Tarif Nr. 7)",
    "zh": "庭审代理（第7号资费）",
    "sr": "Zastupanje na ročištima (tarifni br. 7)",
    "tr": "Duruşmalarda temsil (tarife no. 7)",
    "bs": "Zastupanje na ročištima (tarifni br. 7)",
}
_PAUSHALL_LABEL = {
    "sq": "Paushalli 30% (Tarifa e OAK)",
    "en": "30% flat add-on (OAK tariff)",
    "de": "30% Pauschale (OAK-Tarif)",
    "zh": "30%固定附加费（律师公会资费）",
    "sr": "Paušal 30% (tarifa AKK)",
    "tr": "%30 götürü ek (Baro tarifesi)",
    "bs": "Paušal 30% (tarifa AKK)",
}


def _round(x: Decimal) -> Decimal:
    return x.quantize(_CENT, rounding=ROUND_HALF_UP)


def oak_action_fee(value: Decimal) -> Decimal:
    """OAK tariff amount per submission or hearing for a dispute value."""
    for upper, amount in _OAK_BANDS:
        if value <= upper:
            return amount
    return _OAK_TOP


def court_fee_first_instance(value: Decimal, track: str = "civil") -> Decimal:
    """First-instance court fee per UA 03/2025 for the given track."""
    table = XK_COURT_FEE_TABLE["tracks"][track]
    for low, high, fee in table["bands"]:
        if Decimal(low) < value <= Decimal(high):
            return Decimal(fee)
    above = table["above"]
    pct_fee = _round(value * Decimal(above["percentage"]) / 100)
    return min(pct_fee, Decimal(above["cap"]))


def _lawyer_cost(action_fee: Decimal, instance: dict, vat_rate: int) -> dict:
    """One lawyer's statutory cost in one instance: submission + hearings
    per the OAK tariff, 30% paushall, VAT on top."""
    lines = [
        {
            "vv": "Nr. 6",
            "rate": None,
            "name": instance["submission_label"],
            "amount": str(action_fee),
        }
    ]
    fees = action_fee
    hearings = instance["hearings"]
    if hearings:
        hearing_total = _round(action_fee * hearings)
        fees += hearing_total
        lines.append(
            {
                "vv": "Nr. 7",
                "rate": f"×{hearings}",
                "name": _HEARING_LABEL,
                "amount": str(hearing_total),
            }
        )
    paushall = _round(fees * _PAUSHALL)
    fees += paushall
    lines.append(
        {"vv": "Paushall", "rate": None, "name": _PAUSHALL_LABEL, "amount": str(paushall)}
    )
    vat = _round(fees * Decimal(vat_rate) / 100)
    return {
        "lines": lines,
        "net": str(fees),
        "vat": str(vat),
        "total": str(_round(fees + vat)),
    }


def cost_risk(
    value: Decimal,
    track: str = "civil",
    instance_codes: list[str] | None = None,
    vat_rate: int = 18,
) -> dict:
    """Cost risk per instance and cumulative, loser-pays model (LPK).

    Per instance: own lawyer (OAK tariff + VAT), opponent's lawyer (same
    statutory amounts) and the court fee (UA 03/2025 band × instance rate,
    no VAT). Informative simplification, mirrors the DE cost_risk shape."""
    if track not in XK_COURT_FEE_TABLE["tracks"]:
        track = "civil"
    codes = instance_codes or [i["code"] for i in XK_COST_RISK_INSTANCES]
    base_court = court_fee_first_instance(value, track)
    action_fee = oak_action_fee(value)

    instances = []
    cumulative = Decimal(0)
    for code in codes:
        inst = INSTANCES_BY_CODE.get(code)
        if inst is None:
            continue
        lawyer = _lawyer_cost(action_fee, inst, vat_rate)
        court = _round(base_court * Decimal(inst["court_rate"]))
        lose = Decimal(lawyer["total"]) * 2 + court
        cumulative += lose
        instances.append(
            {
                "code": inst["code"],
                "name": inst["name"],
                "court_kv": "UA 03/2025",
                "court_rate": inst["court_rate"],
                "court_note": inst["court_note"],
                "court_fee": str(court),
                "own_lawyer": lawyer,
                "opponent_lawyer_total": lawyer["total"],
                "total_if_lose": str(_round(lose)),
                "cumulative_if_lose": str(_round(cumulative)),
            }
        )

    return {
        "value": str(value),
        "track": track,
        "oak_action_fee": str(action_fee),
        "court_fee_first_instance": str(base_court),
        "vat_rate": vat_rate,
        "legal_basis": (
            f"{XK_COURT_FEE_TABLE['legal_basis']}; Tarifa e OAK "
            f"(nr. tarifor 6 dhe 7); nenet 449 dhe 452 të LPK-së"
        ),
        # The claimant advances the first-instance fee — without it the
        # claim is dismissed (neni 253.4 i LPK-së).
        "court_fee_advance": str(base_court),
        "instances": instances,
        "total_risk": str(_round(cumulative)),
    }
