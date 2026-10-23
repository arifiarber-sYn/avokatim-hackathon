"""EDA export for the automatisiertes gerichtliches Mahnverfahren (D-059 F7).

Generates the EDA data set for an "Antrag auf Erlass eines Mahnbescheids"
from an overdue invoice: the office (Antragsteller) claims its fee from
the invoiced client (Antragsgegner). Record structures, the Mahngericht
routing table and the claim catalog live HERE AS DATA (hard rule §5.4) —
not scattered through code.

BETA, by design: the record layout follows the public "Bedingungen für die
maschinelle Bearbeitung im automatisierten Mahnverfahren" (fixed 128-char
records, uppercase, DIN-5007 transliteration, amounts in cents, dates
TTMMJJJJ), but without access to a Mahngericht we cannot certify the file
end-to-end. Tests validate the structure against the spec; submission goes
through the office's own EGVP/beA client, and the summary PDF is what the
lawyer reviews before filing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models import Contact, Invoice, Tenant

RECORD_LENGTH = 128

# --- Mahngericht routing: every Bundesland has ONE central Mahngericht ---
# (source: mahngerichte.de; several courts serve multiple Länder)
MAHNGERICHTE: dict[str, dict] = {
    "BW": {"name": "Amtsgericht Stuttgart – Zentrales Mahngericht", "city": "Stuttgart"},
    "BY": {"name": "Amtsgericht Coburg – Zentrales Mahngericht", "city": "Coburg"},
    "BE": {"name": "Amtsgericht Wedding – Zentrales Mahngericht Berlin-Brandenburg", "city": "Berlin"},
    "BB": {"name": "Amtsgericht Wedding – Zentrales Mahngericht Berlin-Brandenburg", "city": "Berlin"},
    "HB": {"name": "Amtsgericht Bremen – Mahngericht", "city": "Bremen"},
    "HH": {"name": "Amtsgericht Hamburg-Altona – Gemeinsames Mahngericht der Länder Hamburg und Mecklenburg-Vorpommern", "city": "Hamburg"},
    "MV": {"name": "Amtsgericht Hamburg-Altona – Gemeinsames Mahngericht der Länder Hamburg und Mecklenburg-Vorpommern", "city": "Hamburg"},
    "HE": {"name": "Amtsgericht Hünfeld – Zentrales Mahngericht", "city": "Hünfeld"},
    "NI": {"name": "Amtsgericht Uelzen – Zentrales Mahngericht", "city": "Uelzen"},
    "NW": {"name": "Amtsgericht Hagen – Zentrales Mahngericht (PLZ 4/5)", "city": "Hagen"},
    "RP": {"name": "Amtsgericht Mayen – Zentrales Mahngericht Rheinland-Pfalz und Saarland", "city": "Mayen"},
    "SL": {"name": "Amtsgericht Mayen – Zentrales Mahngericht Rheinland-Pfalz und Saarland", "city": "Mayen"},
    "SN": {"name": "Amtsgericht Aschersleben – Gemeinsames Mahngericht der Länder Sachsen, Sachsen-Anhalt und Thüringen", "city": "Aschersleben"},
    "ST": {"name": "Amtsgericht Aschersleben – Gemeinsames Mahngericht der Länder Sachsen, Sachsen-Anhalt und Thüringen", "city": "Aschersleben"},
    "TH": {"name": "Amtsgericht Aschersleben – Gemeinsames Mahngericht der Länder Sachsen, Sachsen-Anhalt und Thüringen", "city": "Aschersleben"},
    "SH": {"name": "Amtsgericht Schleswig – Zentrales Mahngericht", "city": "Schleswig"},
}

# --- Hauptforderungskatalog (excerpt) — the claim we generate is always
# the lawyer's fee, but the catalog stays extensible data.
CLAIM_CATALOG: dict[int, str] = {
    19: "Rechtsanwalts-/Rechtsbeistandshonorar",
    43: "Dienstleistungsvertrag",
    90: "Sonstiger Anspruch",
}
FEE_CATALOG_NR = 19

# Statutory default interest (§ 288 BGB), as data: percentage points above
# the Basiszinssatz. Consumers 5, businesses 9 — we default to 5 and let
# the lawyer adjust before filing (the summary PDF says so).
DEFAULT_INTEREST_POINTS = 5

# --- Record layouts: ordered (field, width) pairs. Sum of widths must be
# RECORD_LENGTH - 2 (2 chars go to the leading Satzart).
LAYOUTS: dict[str, list[tuple[str, int]]] = {
    # File header: who files, when, for which court
    "VS": [("absender", 50), ("gericht", 50), ("datum", 8), ("version", 4), ("filler", 14)],
    # Antragsteller (creditor) = the law office
    "01": [("name", 50), ("strasse", 40), ("plz", 5), ("ort", 25), ("kz_firma", 1), ("filler", 5)],
    # Antragsgegner (debtor) = the invoiced client
    "04": [("name", 50), ("strasse", 40), ("plz", 5), ("ort", 25), ("kz_firma", 1), ("filler", 5)],
    # Anspruch (one main claim from the invoice)
    "05": [("katalog_nr", 2), ("bezeichnung", 40), ("rechnung_nr", 20), ("rechnung_datum", 8),
           ("betrag_cent", 12), ("zins_punkte", 2), ("zins_ab", 8), ("filler", 34)],
    # Abschluss: totals + procedural flags
    "07": [("summe_cent", 12), ("kz_streitiges_verfahren", 1), ("kz_zustellung_pza", 1),
           ("anzahl_ansprueche", 3), ("filler", 109)],
    # File trailer: record count
    "NS": [("anzahl_saetze", 6), ("summe_cent", 12), ("filler", 108)],
}

_TRANSLIT = str.maketrans({
    "Ä": "AE", "Ö": "OE", "Ü": "UE", "ä": "AE", "ö": "OE", "ü": "UE",
    "ß": "SS", "é": "E", "è": "E", "ç": "C", "ë": "E",
})


def eda_text(value: str, width: int) -> str:
    """Uppercase, DIN-transliterated, ASCII-safe, space-padded to width."""
    text = str(value or "").translate(_TRANSLIT).upper()
    text = re.sub(r"[^A-Z0-9 .,/&+*()\-]", " ", text)
    return text[:width].ljust(width)


def eda_number(value: int, width: int) -> str:
    return str(max(0, int(value)))[:width].rjust(width, "0")


def eda_date(d: date | None) -> str:
    return f"{d:%d%m%Y}" if d else "0" * 8


def cents(amount: Decimal | float) -> int:
    return int(round(Decimal(str(amount)) * 100))


def split_de_address(address: str | None) -> tuple[str, str, str]:
    """'Musterstraße 12, 10115 Berlin' -> (street, plz, city). Fields the
    regex cannot find stay empty — the lawyer completes them at filing."""
    text = (address or "").replace("\n", ", ").strip()
    match = re.search(r"(\d{5})\s+([^,]+)$", text)
    if not match:
        return text, "", ""
    street = text[: match.start()].strip().rstrip(",").strip()
    return street, match.group(1), match.group(2).strip()


def build_record(satzart: str, values: dict) -> str:
    """One fixed-width record; unknown fields raise, missing ones pad."""
    fields = LAYOUTS[satzart]
    known = {name for name, _ in fields}
    unknown = set(values) - known
    if unknown:
        raise ValueError(f"Unknown EDA fields for {satzart}: {unknown}")
    parts = [eda_text(satzart, 2)]
    for name, width in fields:
        raw = values.get(name, "")
        if isinstance(raw, int) and name != "filler":
            parts.append(eda_number(raw, width))
        else:
            parts.append(eda_text(str(raw), width))
    record = "".join(parts)
    assert len(record) == RECORD_LENGTH, f"{satzart}: {len(record)}"
    return record


@dataclass
class MahnEda:
    records: list[str]
    court: dict
    total_cents: int
    warnings: list[str]

    def as_text(self) -> str:
        return "\r\n".join(self.records) + "\r\n"


def build_mahn_eda(
    *, invoice: Invoice, tenant: Tenant, contact: Contact
) -> MahnEda:
    """The EDA data set for one overdue invoice (fee claim office->client)."""
    warnings: list[str] = []
    region = (tenant.region or "").upper()
    court = MAHNGERICHTE.get(region)
    if court is None:
        court = {"name": "Zentrales Mahngericht (Bundesland wählen)", "city": ""}
        warnings.append(
            "Zyra s'ka Bundesland të vendosur (Cilësimet) — gjykata e "
            "Mahnverfahren s'mund të përcaktohet automatikisht."
        )

    t_street, t_plz, t_city = split_de_address(tenant.address)
    if not t_plz:
        warnings.append("Adresa e zyrës s'ka PLZ të lexueshme — plotësoje para dorëzimit.")
    c_street, c_plz, c_city = split_de_address(contact.address)
    if not c_plz:
        warnings.append("Adresa e klientit s'ka PLZ të lexueshme — plotësoje para dorëzimit.")

    total = cents(invoice.total_with_vat)
    interest_from = invoice.due_on or date.today()

    records = [
        build_record("VS", {
            "absender": tenant.name,
            "gericht": court["name"],
            "datum": eda_date(date.today()),
            "version": "1.0",
        }),
        build_record("01", {
            "name": tenant.name,
            "strasse": t_street,
            "plz": t_plz,
            "ort": t_city,
            "kz_firma": "J",  # the office is always an organization
        }),
        build_record("04", {
            "name": contact.display_name,
            "strasse": c_street,
            "plz": c_plz,
            "ort": c_city,
            "kz_firma": "J" if contact.kind == "organization" else "N",
        }),
        build_record("05", {
            "katalog_nr": FEE_CATALOG_NR,
            "bezeichnung": CLAIM_CATALOG[FEE_CATALOG_NR],
            "rechnung_nr": invoice.number,
            "rechnung_datum": eda_date(invoice.issued_on),
            "betrag_cent": total,
            "zins_punkte": DEFAULT_INTEREST_POINTS,
            "zins_ab": eda_date(interest_from),
        }),
        build_record("07", {
            "summe_cent": total,
            "kz_streitiges_verfahren": "J",  # hand over to litigation on objection
            "kz_zustellung_pza": "N",
            "anzahl_ansprueche": 1,
        }),
    ]
    records.append(
        build_record("NS", {"anzahl_saetze": len(records) + 1, "summe_cent": total})
    )
    return MahnEda(records=records, court=court, total_cents=total, warnings=warnings)


# ---------- the human-readable summary the lawyer reviews ----------

_SUMMARY_PAGE = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: "DejaVu Sans", sans-serif; color: #1a2233; font-size: 11px; line-height: 1.55; }}
  h1 {{ font-size: 17px; margin-bottom: 2px; }}
  .beta {{ display: inline-block; background: #fef3c7; color: #92400e; font-weight: bold;
          border-radius: 8px; padding: 2px 10px; font-size: 10px; }}
  h2 {{ font-size: 12px; margin: 18px 0 6px; color: #4338ca; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td {{ padding: 4px 8px; border: 1px solid #dfe3ea; vertical-align: top; }}
  td.k {{ width: 34%; color: #556; }}
  .warn {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px;
          padding: 8px 12px; color: #991b1b; margin-top: 12px; }}
  .note {{ margin-top: 16px; color: #556; font-size: 10px; }}
</style></head>
<body>
  <h1>Antrag auf Erlass eines Mahnbescheids — Zusammenfassung</h1>
  <span class="beta">BETA — EDA-Datensatz, Einreichung über Ihren EGVP/beA-Zugang</span>

  <h2>Zuständiges Mahngericht</h2>
  <table><tr><td class="k">Gericht</td><td>{court}</td></tr></table>

  <h2>Antragsteller (Gläubiger)</h2>
  <table>
    <tr><td class="k">Name</td><td>{as_name}</td></tr>
    <tr><td class="k">Anschrift</td><td>{as_addr}</td></tr>
  </table>

  <h2>Antragsgegner (Schuldner)</h2>
  <table>
    <tr><td class="k">Name</td><td>{ag_name}</td></tr>
    <tr><td class="k">Anschrift</td><td>{ag_addr}</td></tr>
  </table>

  <h2>Anspruch</h2>
  <table>
    <tr><td class="k">Hauptforderung (Katalog-Nr. {kat_nr})</td><td>{kat_name}</td></tr>
    <tr><td class="k">Rechnung</td><td>{re_nr} vom {re_datum}</td></tr>
    <tr><td class="k">Betrag</td><td>{betrag} €</td></tr>
    <tr><td class="k">Verzugszinsen</td><td>{zins} Prozentpunkte über Basiszins seit {zins_ab}</td></tr>
  </table>

  {warnings_html}

  <p class="note">Die beigefügte .eda-Datei folgt der Satzstruktur der
  „Bedingungen für die maschinelle Bearbeitung im automatisierten
  Mahnverfahren". Prüfen Sie die Angaben und reichen Sie den Antrag über
  Ihren EGVP-/beA-Zugang beim zuständigen Mahngericht ein. Alternativ:
  online-mahnantrag.de mit denselben Daten.</p>
</body></html>"""


def build_summary_pdf(
    *, eda: MahnEda, invoice: Invoice, tenant: Tenant, contact: Contact
) -> bytes:
    import html as html_mod

    from weasyprint import HTML

    esc = lambda v: html_mod.escape(str(v or "—"))  # noqa: E731
    warnings_html = ""
    if eda.warnings:
        items = "".join(f"<div>⚠ {esc(w)}</div>" for w in eda.warnings)
        warnings_html = f'<div class="warn">{items}</div>'
    page = _SUMMARY_PAGE.format(
        court=esc(eda.court["name"]),
        as_name=esc(tenant.name),
        as_addr=esc(tenant.address),
        ag_name=esc(contact.display_name),
        ag_addr=esc(contact.address),
        kat_nr=FEE_CATALOG_NR,
        kat_name=esc(CLAIM_CATALOG[FEE_CATALOG_NR]),
        re_nr=esc(invoice.number),
        re_datum=esc(f"{invoice.issued_on:%d.%m.%Y}" if invoice.issued_on else "—"),
        betrag=f"{eda.total_cents / 100:.2f}",
        zins=DEFAULT_INTEREST_POINTS,
        zins_ab=esc(f"{invoice.due_on:%d.%m.%Y}" if invoice.due_on else "—"),
        warnings_html=warnings_html,
    )
    return HTML(string=page).write_pdf()
