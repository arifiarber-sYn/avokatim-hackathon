"""DATEV EXTF Buchungsstapel export (D-037 phase 4)."""
from datetime import date
from decimal import Decimal

from app.models import Invoice, InvoiceItem
from app.services.datev import (
    Booking,
    DatevConfig,
    bookings_for_invoices,
    build_extf,
)


def _invoice(number: str, issued: date | None, paid: date | None) -> Invoice:
    inv = Invoice(number=number, currency="EUR", vat_rate=19,
                  issued_on=issued, paid_on=paid)
    inv.items = [
        InvoiceItem(description="Honorar", quantity=Decimal("1"),
                    unit_price=Decimal("500.00"))
    ]
    return inv


def test_bookings_issued_and_paid():
    config = DatevConfig()
    invoices = [
        _invoice("RE-1", date(2026, 7, 3), date(2026, 7, 20)),
        _invoice("RE-2", date(2026, 6, 20), None),  # issued outside period
    ]
    bookings = bookings_for_invoices(
        invoices, config, date(2026, 7, 1), date(2026, 7, 31)
    )
    assert len(bookings) == 2  # RE-1 issue + RE-1 payment; RE-2 excluded
    issue, payment = bookings
    assert issue.account == "10000" and issue.contra_account == "8400"
    assert payment.account == "1200" and payment.contra_account == "10000"
    assert issue.amount == Decimal("595.00")  # 500 + 19 % USt


def test_extf_structure_and_encoding():
    config = DatevConfig(consultant_no="12345", client_no="678")
    csv = build_extf(
        [
            Booking(
                amount=Decimal("595.00"), debit_credit="S", account="10000",
                contra_account="8400", doc_date=date(2026, 7, 3),
                doc_field1="RE-1", text="Rechnung RE-1 Müller GmbH",
            )
        ],
        config, date(2026, 7, 1), date(2026, 7, 31),
    )
    text = csv.decode("cp1252")
    lines = text.strip().split("\r\n")
    assert lines[0].startswith('"EXTF";700;21;"Buchungsstapel";13;')
    assert ";12345;678;" in lines[0]
    assert lines[1].startswith("Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen")
    assert lines[2].startswith('595,00;"S";"EUR";')  # decimal comma
    assert "0307" in lines[2]  # Belegdatum DDMM
    assert "Müller" in text  # cp1252 keeps umlauts
