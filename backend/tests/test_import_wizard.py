"""Migration wizard (D-059 F3): CSV/XLSX parsing, preset column mapping and
normalization — the pure logic under /import/preview and the importers."""
import io

import pytest
from fastapi import HTTPException
from openpyxl import Workbook

from app.api.imports import (
    AREA_ALIASES,
    STATUS_ALIASES,
    _normalize,
    _parse_mapping,
    _read_csv,
    _read_rows,
)


def test_csv_semicolon_delimiter_detected():
    rows = _read_csv(b"Name;E-Mail;Telefon\nKrasniqi Arben;a@b.de;+383 44 1\n")
    assert rows == [{"name": "Krasniqi Arben", "e-mail": "a@b.de", "telefon": "+383 44 1"}]


def test_xlsx_roundtrip():
    wb = Workbook()
    ws = wb.active
    ws.append(["display_name", "email"])
    ws.append(["Blerta Gashi", "blerta@shembull.com"])
    buf = io.BytesIO()
    wb.save(buf)
    rows = _read_rows("kontaktet.xlsx", buf.getvalue())
    assert rows == [{"display_name": "Blerta Gashi", "email": "blerta@shembull.com"}]


def test_ra_micro_matters_preset_maps_aktenzeichen_and_gegner():
    rows = [
        {
            "aktenzeichen": "12/26 M01",
            "wegen": "Kündigungsschutzklage",
            "referat": "Arbeitsrecht",
            "mandant": "Arben Krasniqi",
            "gegner": "Müller GmbH",
            "gericht": "ArbG Köln",
            "angelegt": "15.01.2026",
            "aktenstatus": "offen",
        }
    ]
    normalized, mapping, unmapped = _normalize(rows, "matters", "ra_micro", None)
    row = normalized[0]
    assert row["legacy_reference"] == "12/26 M01"
    assert row["title"] == "Kündigungsschutzklage"
    assert row["client_name"] == "Arben Krasniqi"
    assert row["opposing_party"] == "Müller GmbH"
    assert row["court_name"] == "ArbG Köln"
    assert AREA_ALIASES[row["practice_area"].lower()] == "labor"
    assert STATUS_ALIASES[row["status"].lower()] == "open"
    assert unmapped == []


def test_generic_contacts_composes_name_and_address_from_german_split_columns():
    rows = [
        {
            "vorname": "Arben",
            "nachname": "Krasniqi",
            "straße": "Hauptstr. 5",
            "plz": "50667",
            "ort": "Köln",
            "e-mail": "arben@example.com",
        }
    ]
    normalized, _, _ = _normalize(rows, "contacts", "generic", None)
    row = normalized[0]
    assert row["display_name"] == "Arben Krasniqi"
    assert row["address"] == "Hauptstr. 5, 50667 Köln"
    assert row["email"] == "arben@example.com"


def test_custom_mapping_overrides_and_ignores():
    rows = [{"spalte_x": "Kontest pronësor", "spalte_y": "irrelevant", "status": "hapur"}]
    normalized, mapping, unmapped = _normalize(
        rows, "matters", "generic", {"spalte_x": "title", "spalte_y": ""}
    )
    assert normalized[0]["title"] == "Kontest pronësor"
    assert mapping["spalte_x"] == "title"
    assert "spalte_y" in unmapped or "spalte_y" not in mapping


def test_parse_mapping_rejects_non_object():
    assert _parse_mapping(None) is None
    assert _parse_mapping('{"a": "title"}') == {"a": "title"}
    with pytest.raises(HTTPException):
        _parse_mapping("[1,2]")
    with pytest.raises(HTTPException):
        _parse_mapping("not json")
