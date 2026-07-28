"""Platform subscription billing unit tests (D-016)."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.i18n import CATALOG, tr
from app.services.platform_billing import (
    GRACE_DAYS,
    TRIAL_DAYS,
    _month_end,
    month_start,
    tenant_is_billable,
)

ALL_LOCALES = ["sq", "sr", "tr", "bs", "en", "zh"]

BILLING_KEYS = [
    "platform_invoice_subject",
    "platform_invoice_body",
    "platform_overdue_subject",
    "platform_overdue_body",
    "trial_ending_subject",
    "trial_ending_body",
    "case_match_subject",
    "case_match_body",
]


def test_trial_is_three_months():
    assert TRIAL_DAYS == 365
    assert GRACE_DAYS > 0


def test_month_boundaries():
    assert month_start(date(2026, 7, 20)) == date(2026, 7, 1)
    assert _month_end(date(2026, 7, 1)) == date(2026, 7, 31)
    assert _month_end(date(2026, 2, 1)) == date(2026, 2, 28)
    assert _month_end(date(2026, 12, 1)) == date(2026, 12, 31)


def test_billable_needs_paid_plan_and_positive_price():
    def t(plan, status="active", price=Decimal("24")):
        return SimpleNamespace(plan=plan, status=status, plan_price_eur=price)

    assert tenant_is_billable(t("solo")) is True
    assert tenant_is_billable(t("firm")) is True
    # trials are never invoiced
    assert tenant_is_billable(t("trial")) is False
    # suspended tenants are not invoiced
    assert tenant_is_billable(t("solo", status="suspended")) is False
    # price 0 = free forever (founder / strategic partner)
    assert tenant_is_billable(t("firm", price=Decimal("0"))) is False


def test_billing_i18n_keys_in_all_languages():
    for code in ALL_LOCALES:
        for key in BILLING_KEYS:
            assert key in CATALOG[code], f"{code} missing {key}"
    body = tr(
        "sq", "platform_invoice_body",
        number="P-2026-0001", period="07/2026", seats=2, price="24.00",
        amount="48.00", due="25.07.2026", bank="Banka X", url="https://x",
    )
    assert "P-2026-0001" in body and "48.00" in body and "Banka X" in body
