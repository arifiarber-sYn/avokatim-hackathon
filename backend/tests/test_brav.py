"""Tests for the BRAV portal client (parsing + name matching).

The fixtures are trimmed real partial-responses recorded from
bravsearch.bea-brak.de on 2026-08-01.
"""
from pathlib import Path

from app.services.brav import (
    BravEntry,
    de_names_match,
    normalize_de_name,
    parse_search_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestParseResults:
    def test_parses_total_and_cards(self):
        result = parse_search_response(_load("brav_results.xml"))
        assert result is not None
        assert result.total == 11
        assert len(result.entries) == 2
        assert result.truncated  # 11 total, only the first page parsed

    def test_first_card_without_office(self):
        entry = parse_search_response(_load("brav_results.xml")).entries[0]
        assert entry.last_name == "Müller"
        assert entry.first_name == "Juliane Katharina"
        assert entry.profession == "Rechtsanwältin"
        assert entry.office == ""
        assert entry.street == "Schubertstr. 6"
        assert entry.postal_code == "64859"
        assert entry.city == "Eppertshausen"
        assert entry.full_name == "Juliane Katharina Müller"

    def test_second_card_with_office(self):
        entry = parse_search_response(_load("brav_results.xml")).entries[1]
        assert entry.first_name == "Katharina"
        assert entry.office == "Müller"
        assert entry.city == "Koblenz"
        assert "Rechtsanwältin" in entry.describe()
        assert "Koblenz" in entry.describe()

    def test_no_result_dialog_means_zero(self):
        result = parse_search_response(_load("brav_no_result.xml"))
        assert result is not None
        assert result.total == 0
        assert result.entries == []
        assert not result.truncated

    def test_unrecognized_payload_returns_none(self):
        assert parse_search_response("<html>beA-Störung</html>") is None
        assert parse_search_response("") is None


class TestNameNormalization:
    def test_umlauts_fold_to_two_letter_form(self):
        assert normalize_de_name("Müller") == "mueller"
        assert normalize_de_name("Groß") == "gross"
        assert normalize_de_name("Öztürk") == "oeztuerk"

    def test_titles_are_stripped(self):
        assert normalize_de_name("Dr. Thomas Müller") == "thomas mueller"
        assert normalize_de_name("Prof. Dr. Anna Weber, LL.M.") == "anna weber"

    def test_accents_are_stripped(self):
        assert normalize_de_name("José García") == "jose garcia"


class TestNamesMatch:
    def test_exact_and_umlaut_spellings(self):
        assert de_names_match("Katharina Müller", "Katharina Mueller")
        assert de_names_match("Katharina Muller", "Katharina Müller")

    def test_order_and_comma_insensitive(self):
        assert de_names_match("Müller Katharina", "Katharina Müller")
        assert de_names_match("Müller, Katharina", "Katharina Müller")

    def test_titles_ignored(self):
        assert de_names_match("Dr. Katharina Müller", "Katharina Müller")

    def test_different_people_do_not_match(self):
        assert not de_names_match("Katharina Müller", "Juliane Katharina Müller")
        assert not de_names_match("Katharina Müller", "Katharina Meier")
        assert not de_names_match("", "")
        assert not de_names_match("", "Katharina Müller")


def test_brav_entry_full_name_handles_missing_first_name():
    e = BravEntry(last_name="Müller", first_name="", profession="Rechtsanwalt")
    assert e.full_name == "Müller"
