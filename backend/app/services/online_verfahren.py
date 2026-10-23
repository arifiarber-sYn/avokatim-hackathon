"""Zivilgerichtliches Online-Verfahren (D-041): eligibility check and data
assembly for Germany's new civil online procedure (live 2026-04-15,
service.justiz.de). The pilot courts and their scopes are data in
`seeds/germany.py`; this module only evaluates.

The procedure covers payment claims up to 10,000 € (Amtsgericht ceiling)
filed by citizens acting non-commercially; lawyers may use it too. Some
pilot courts accept only air-passenger-rights claims. Court fees in the
online procedure are reduced: 2.0 instead of 3.0 (KV GKG)."""
from decimal import Decimal

from app.seeds.germany import DE_OV_COURTS, OV_MAX_VALUE, OV_PORTAL_URL
from app.services.prozesskosten import court_fee_unit

_FLIGHT_WORDS = ("flug", "flight", "airline", "fluggast", "annullier", "261/2004")


def _norm(s: str) -> str:
    return " ".join(s.lower().replace("amtsgericht", "ag").split())


def match_court(court_name: str | None) -> dict | None:
    """Match a matter's court against the pilot list (name containment,
    'Amtsgericht' and 'AG' treated the same)."""
    if not court_name:
        return None
    needle = _norm(court_name)
    for court in DE_OV_COURTS:
        candidate = _norm(court["name"])
        if candidate in needle or needle in candidate:
            return court
    return None


def looks_like_flight_case(*texts: str | None) -> bool:
    blob = " ".join(t.lower() for t in texts if t)
    return any(w in blob for w in _FLIGHT_WORDS)


def check_eligibility(
    *,
    value_eur: Decimal | None,
    court_name: str | None = None,
    title: str | None = None,
    description: str | None = None,
) -> dict:
    """Structured eligibility report. `checks` use stable codes so the UI can
    localize; the lawyer always makes the final call (claim type can't be
    verified automatically)."""
    is_flight = looks_like_flight_case(title, description)
    court = match_court(court_name)

    checks = []
    ok = True

    if value_eur is None:
        checks.append({"code": "value_unknown", "ok": None})
    elif value_eur <= OV_MAX_VALUE:
        checks.append({"code": "value_ok", "ok": True, "value": str(value_eur)})
    else:
        checks.append({"code": "value_too_high", "ok": False, "value": str(value_eur)})
        ok = False

    if court is not None:
        scope_ok = court["scope"] == "payment" or is_flight
        checks.append(
            {
                "code": "court_pilot" if scope_ok else "court_flight_only",
                "ok": scope_ok,
                "court": court,
            }
        )
        ok = ok and scope_ok
    else:
        checks.append({"code": "court_unknown", "ok": None})

    # The claim must be a payment claim (money only) — not verifiable
    # automatically, surfaced as a manual confirmation point.
    checks.append({"code": "payment_claim_manual", "ok": None})

    fees = None
    if value_eur is not None and value_eur > 0:
        cent = Decimal("0.01")
        unit = court_fee_unit(value_eur)
        fees = {
            "regular_advance": str((unit * 3).quantize(cent)),  # KV 1210
            "ov_advance": str((unit * 2).quantize(cent)),  # reduced OV rate
            "saving": str(unit.quantize(cent)),
        }

    return {
        "eligible": ok,
        "is_flight_case": is_flight,
        "suggested_template": (
            "civil.ov_fluggastrechte" if is_flight else "civil.ov_klageschrift"
        ),
        "checks": checks,
        "matched_court": court,
        "courts": DE_OV_COURTS,
        "max_value": OV_MAX_VALUE,
        "portal_url": OV_PORTAL_URL,
        "fees": fees,
    }


def export_payload(matter, variables: dict, value_eur: Decimal | None) -> dict:
    """Structured claim data for a future XJustiz submission: the fields the
    justice portal asks for, assembled from the matter file. Format-neutral
    JSON until the BMJV publishes the lawyer-side submission spec."""
    return {
        "schema": "avokatim.ov-export/v1",
        "procedure": "zivilgerichtliches-online-verfahren",
        "claim_type": (
            "fluggastrechte"
            if looks_like_flight_case(matter.title, matter.description)
            else "zahlungsklage"
        ),
        "court": matter.court_name,
        "value_eur": str(value_eur) if value_eur is not None else None,
        "claimant": {
            "name": variables.get("client_name"),
            "address": variables.get("client_address"),
        },
        "defendant": {"name": variables.get("opposing_name")},
        "representative": {"name": variables.get("lawyer_name")},
        "reference": matter.reference,
        "subject": matter.title,
        "facts": matter.description,
        "portal_url": OV_PORTAL_URL,
    }
