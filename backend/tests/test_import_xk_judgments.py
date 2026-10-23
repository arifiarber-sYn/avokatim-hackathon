"""Parser tests for the Kosovo judgments importer (D-050, B3): listing rows,
Albanian-PDF-only filtering, dates, references and titles — against a trimmed
fixture recorded from gjyqesori-rks.org/aktgjykimet/ (Supreme filter)."""
from datetime import date
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.import_xk_judgments import (  # noqa: E402
    _parse_date,
    build_reference,
    build_title,
    parse_listing,
)

FIXTURE = Path(__file__).parent / "fixtures" / "xk_judgments_listing.html"


def _rows():
    return parse_listing(FIXTURE.read_text())


def test_total_count_parsed():
    _, total = _rows()
    assert total == 21241


def test_rows_parsed_with_fields():
    rows, _ = _rows()
    assert rows, "fixture should yield rows"
    first = rows[0]
    assert first["type_code"] == "PZD"
    assert first["type_label"] == "Zbutje e Denimit Penal"
    assert first["case_no"] == "53/2026"
    assert first["decided"] == date(2026, 6, 10)
    assert first["published"] == date(2026, 7, 23)
    assert first["judge"] == "Agim Maliqi"
    assert first["court"] == "Gjykata Supreme"
    assert first["pdf_url"].endswith("/wp-content/uploads/verdicts/SUP_PZD_2023-211231_SQ.pdf")
    assert first["pdf_url"].startswith("https://www.gjyqesori-rks.org/")


def test_serbian_only_rows_are_dropped():
    rows, _ = _rows()
    # The fixture contains a PML 551/2026 row whose only PDF is _SR — the
    # importer keeps the corpus Albanian, so that row must not appear.
    assert all("_SQ.pdf" in r["pdf_url"] for r in rows)
    assert not any(r["case_no"] == "551/2026" for r in rows)


def test_reference_prefers_official_designation_from_pdf():
    row = {"type_code": "PZD", "case_no": "53/2026"}
    text = "REPUBLIKA E KOSOVËS\nNumri i lëndës: 2025:169963\nPPP.nr.59/2025\nGJYKATA..."
    assert build_reference(row, text) == "PPP.nr.59/2025"


def test_reference_falls_back_to_row_data():
    row = {"type_code": "PZD", "case_no": "53/2026"}
    assert build_reference(row, "tekst pa numër lënde të dallueshëm") == "PZD.nr. 53/2026"
    # A row case number that already carries its prefix is kept verbatim.
    row2 = {"type_code": "PPP", "case_no": "PPP.nr. 59/25"}
    assert build_reference(row2, "asgjë") == "PPP.nr. 59/25"


def test_title_includes_court_label_and_date():
    row = {
        "court": "Gjykata Supreme",
        "type_label": "Zbutje e Denimit Penal",
        "decided": date(2026, 6, 10),
    }
    assert build_title(row, "PZD.nr. 53/2026") == (
        "Gjykata Supreme, Zbutje e Denimit Penal — PZD.nr. 53/2026, 10.06.2026"
    )


def test_parse_date_handles_garbage():
    assert _parse_date("23/07/2026") == date(2026, 7, 23)
    assert _parse_date("") is None
    assert _parse_date("s'ka datë") is None
