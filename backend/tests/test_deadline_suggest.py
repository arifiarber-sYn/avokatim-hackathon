"""Unit tests for the deadline-suggestion service (D-043)."""
import uuid

from app.services.deadline_suggest import _parse_date, match_rule


class FakeRule:
    def __init__(self, code, legal_basis, name, days=14):
        self.id = uuid.uuid4()
        self.code = code
        self.legal_basis = legal_basis
        self.name = name
        self.days = days


RULES = [
    FakeRule("civil.appeal", "LPK neni 176", {"sq": "Afati i ankesës (civile)"}),
    FakeRule("de.civil.berufung", "§ 517 ZPO", {"de": "Berufungsfrist", "sq": "Afati i apelit"}),
    FakeRule("de.labor.kschg", "§ 4 KSchG", {"de": "Kündigungsschutzklage"}),
]


def test_matches_rule_by_statute_and_article():
    rule = match_rule(RULES, "§ 517 ZPO", "Frist für die Berufung")
    assert rule is not None and rule.code == "de.civil.berufung"


def test_matches_kosovo_rule():
    rule = match_rule(RULES, "LPK neni 176", "Afati i ankesës")
    assert rule is not None and rule.code == "civil.appeal"


def test_vague_basis_does_not_match():
    # One shared token ("ZPO" alone) is not specific enough
    assert match_rule(RULES, "ZPO", "diçka e papërcaktuar") is None
    assert match_rule(RULES, None, None) is None


def test_title_overlap_can_carry_the_match():
    rule = match_rule(RULES, None, "Kündigungsschutzklage einreichen")
    assert rule is not None and rule.code == "de.labor.kschg"


def test_parse_date():
    from datetime import date

    assert _parse_date("2026-09-15") == date(2026, 9, 15)
    assert _parse_date("2026-09-15T00:00:00") == date(2026, 9, 15)
    assert _parse_date(None) is None
    assert _parse_date("nuk dihet") is None
