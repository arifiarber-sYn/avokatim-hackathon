"""DATEV EXTF export (Buchungsstapel) for German offices — the standard way
a Kanzlei hands its bookkeeping to the Steuerberater. The format is publicly
documented ("DATEV-Format", EXTF header 700 / Buchungsstapel version 13);
no dependency needed.

Two booking types are exported per period:
- issued invoices: debtor account (Soll) against the revenue account, gross;
- received payments: bank account against the debtor account, gross.
Accounts default to SKR03 (8400 revenue 19 % USt — an "Automatikkonto", so
no BU-Schlüssel is set; 1200 bank; 10000 debtor) and are overridable per
tenant in the settings."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

DEFAULT_REVENUE_ACCOUNT = "8400"  # SKR03: Erlöse 19 % USt (Automatikkonto)
DEFAULT_DEBTOR_ACCOUNT = "10000"  # first collective debtor account
BANK_ACCOUNT = "1200"  # SKR03: Bank


@dataclass
class DatevConfig:
    consultant_no: str = ""
    client_no: str = ""
    revenue_account: str = DEFAULT_REVENUE_ACCOUNT
    debtor_account: str = DEFAULT_DEBTOR_ACCOUNT


@dataclass
class Booking:
    amount: Decimal  # gross, positive
    debit_credit: str  # "S" | "H" (relative to `account`)
    account: str
    contra_account: str
    doc_date: date
    doc_field1: str  # invoice number
    text: str


def _num(value: Decimal) -> str:
    """DATEV decimal: comma separator, two places, no thousands sep."""
    return f"{value:.2f}".replace(".", ",")


def _quoted(value: str) -> str:
    return '"' + value.replace('"', "'")[:60] + '"'


def build_extf(
    bookings: list[Booking],
    config: DatevConfig,
    date_from: date,
    date_to: date,
    *,
    now: datetime | None = None,
) -> bytes:
    """The EXTF CSV: metadata header, column header, one row per booking."""
    now = now or datetime.now()
    fy_start = date(date_from.year, 1, 1)  # calendar fiscal year
    header = ";".join(
        [
            '"EXTF"', "700", "21", '"Buchungsstapel"', "13",
            now.strftime("%Y%m%d%H%M%S000"), "", '""', '""', '""',
            config.consultant_no or "0", config.client_no or "0",
            fy_start.strftime("%Y%m%d"), "4",
            date_from.strftime("%Y%m%d"), date_to.strftime("%Y%m%d"),
            '"Ava Legal Export"', '""', "1", "0", "0", '"EUR"',
        ]
    )
    columns = ";".join(
        [
            "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen",
            "WKZ Umsatz", "Kurs", "Basis-Umsatz", "WKZ Basis-Umsatz",
            "Konto", "Gegenkonto (ohne BU-Schlüssel)", "BU-Schlüssel",
            "Belegdatum", "Belegfeld 1", "Belegfeld 2", "Skonto",
            "Buchungstext",
        ]
    )
    rows = [header, columns]
    for b in bookings:
        rows.append(
            ";".join(
                [
                    _num(b.amount), f'"{b.debit_credit}"', '"EUR"', "", "", "",
                    b.account, b.contra_account, '""',
                    b.doc_date.strftime("%d%m"),
                    _quoted(b.doc_field1)[:38], '""', "",
                    _quoted(b.text),
                ]
            )
        )
    # DATEV expects ANSI (Windows-1252) with CRLF line endings
    return ("\r\n".join(rows) + "\r\n").encode("cp1252", errors="replace")


def bookings_for_invoices(
    invoices: list,
    config: DatevConfig,
    date_from: date,
    date_to: date,
    client_names: dict | None = None,
) -> list[Booking]:
    """Issued-invoice and payment bookings for the period, ordered by date."""
    out: list[Booking] = []
    for inv in invoices:
        gross = Decimal(inv.total_with_vat)
        if gross <= 0:
            continue
        client = ((client_names or {}).get(inv.contact_id) or "")[:60]
        if inv.issued_on and date_from <= inv.issued_on <= date_to:
            out.append(
                Booking(
                    amount=gross,
                    debit_credit="S",  # debtor owes us
                    account=config.debtor_account,
                    contra_account=config.revenue_account,
                    doc_date=inv.issued_on,
                    doc_field1=inv.number,
                    text=f"Rechnung {inv.number} {client}".strip(),
                )
            )
        if inv.paid_on and date_from <= inv.paid_on <= date_to:
            out.append(
                Booking(
                    amount=gross,
                    debit_credit="S",  # bank receives
                    account=BANK_ACCOUNT,
                    contra_account=config.debtor_account,
                    doc_date=inv.paid_on,
                    doc_field1=inv.number,
                    text=f"Zahlung {inv.number} {client}".strip(),
                )
            )
    out.sort(key=lambda b: b.doc_date)
    return out
