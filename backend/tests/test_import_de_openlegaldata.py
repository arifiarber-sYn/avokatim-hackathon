"""Parser tests for the openlegaldata instance-court importer (D-059 F2)
and the case-law-aware retrieval cap in rag.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.rag import _wants_case_law  # noqa: E402
from scripts.import_de_openlegaldata import (  # noqa: E402
    html_to_text,
    parse_case,
    practice_area,
)


def _case(**overrides) -> dict:
    base = {
        "id": 1,
        "slug": "lg-koeln-2020-01-15-5-s-9-19",
        "court": {"name": "LG Köln", "jurisdiction": "Ordentliche Gerichtsbarkeit"},
        "file_number": "5 S 9/19",
        "date": "2020-01-15",
        "type": "Urteil",
        "ecli": "ECLI:DE:LGK:2020:0115.5S9.19.00",
        "content": "<h2>Tenor</h2><p>" + "Die Berufung wird zurückgewiesen. " * 40 + "</p>",
    }
    base.update(overrides)
    return base


def test_register_letter_maps_to_practice_area():
    assert practice_area("8 C 123/19") == "civil"      # AG civil
    assert practice_area("12 O 45/20") == "civil"      # LG first instance
    assert practice_area("3 F 78/19") == "family"
    assert practice_area("2 Ca 150/20") == "labor"
    assert practice_area("4 Ss 33/21") is None         # criminal — excluded
    assert practice_area("nonsense") is None


def test_parse_case_builds_corpus_payload():
    parsed = parse_case(_case())
    assert parsed is not None
    assert parsed["reference"] == "LG Köln, 5 S 9/19"  # unique across courts
    assert parsed["title"].startswith("LG Köln, Urteil vom 15.01.2020")
    assert parsed["doc_type"] == "judgment"
    assert parsed["language"] == "de"
    assert parsed["text"].startswith("ECLI: ECLI:DE:LGK:2020")
    assert "Die Berufung wird zurückgewiesen." in parsed["text"]
    assert parsed["area"] == "civil"


def test_parse_case_filters_federal_criminal_and_short():
    # Federal courts come from rechtsprechung-im-internet, not here
    assert parse_case(_case(court={"name": "BGH"})) is None
    # Criminal register excluded
    assert parse_case(_case(file_number="4 Ss 33/21")) is None
    # Too little text to be a useful RAG source
    assert parse_case(_case(content="<p>kurz</p>")) is None


def test_html_to_text_strips_tags_and_entities():
    text = html_to_text("<div><p>§ 543 BGB &amp; § 569</p><br><p>Abs.&nbsp;2</p></div>")
    assert "§ 543 BGB & § 569" in text
    assert "Abs. 2" in text
    assert "<" not in text


def test_wants_case_law_detection():
    assert _wants_case_law("Wie hat der BGH zur Eigenbedarfskündigung entschieden?")
    assert _wants_case_law("Gibt es Rechtsprechung zu § 573 BGB?")
    assert _wants_case_law("A ka praktikë gjyqësore për nenin 176 të LPK?")
    assert not _wants_case_law("Welche Frist gilt für die Berufung?")
    assert not _wants_case_law("Sa është afati i ankesës?")
