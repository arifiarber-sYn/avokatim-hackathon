"""Category intake questionnaires (D-059 F5): seed integrity, the WhatsApp
question flow helpers, and the API-side answer cleaning."""

from app.api.marketplace import clean_structured_answers
from app.seeds.case_intake_questions import (
    CASE_INTAKE_QUESTIONS,
    CONVERSATIONAL_MAX_QUESTIONS,
    choice_label,
    question_label,
    questions_for,
)
from app.services.wa_intake import _parse_answer, _pending_questions, _question_prompt

LOCALES = ("sq", "en", "de", "sr", "tr", "bs", "zh")


def test_seed_integrity_all_locales_and_types():
    assert CASE_INTAKE_QUESTIONS, "seed must not be empty"
    for category, questions in CASE_INTAKE_QUESTIONS.items():
        assert 1 <= len(questions) <= 5, category
        keys = [q["key"] for q in questions]
        assert len(keys) == len(set(keys)), f"duplicate keys in {category}"
        for q in questions:
            assert q["type"] in ("text", "date", "choice"), q["key"]
            for loc in LOCALES:
                assert q["label"].get(loc), f"{category}.{q['key']} missing {loc}"
            if q["type"] == "choice":
                assert q["choices"], q["key"]
                for c in q["choices"]:
                    for loc in LOCALES:
                        assert c["label"].get(loc), f"{q['key']}:{c['value']} missing {loc}"


def test_questions_for_unknown_category_is_empty():
    assert questions_for("other") == []
    assert questions_for("nonexistent") == []


def test_question_and_choice_labels_localized():
    assert question_label("labor", "termination_date", "de").startswith("Wann")
    assert question_label("labor", "termination_date", "sq").startswith("Kur")
    # unknown key falls back to the key itself
    assert question_label("labor", "bogus", "de") == "bogus"
    assert choice_label("family", "separated", "yes", "de") == "Ja"
    # free-text answers pass through unchanged
    assert choice_label("civil", "amount", "5000", "de") == "5000"


def test_clean_structured_answers_drops_unknown_keys():
    cleaned = clean_structured_answers(
        {"termination_date": " 2026-05-01 ", "evil_key": "x", "unpaid_wages": ""},
        "labor",
        "DE",
    )
    assert cleaned == {"termination_date": "2026-05-01"}
    assert clean_structured_answers(None, "labor", "DE") is None
    assert clean_structured_answers({"evil": "x"}, "labor", "DE") is None


def test_wa_pending_questions_capped():
    pending = _pending_questions("family", "XK")
    assert 0 < len(pending) <= CONVERSATIONAL_MAX_QUESTIONS


def test_wa_question_prompt_numbers_choices():
    q = questions_for("criminal")[0]  # role: choice
    prompt = _question_prompt(q, "de")
    assert prompt.startswith("Welche Rolle")
    assert "1)" in prompt and "2)" in prompt


def test_wa_parse_answer_by_number_text_and_freeform():
    q = next(x for x in questions_for("family") if x["key"] == "separated")
    assert _parse_answer(q, "1") == "yes"
    assert _parse_answer(q, "Nein") == "no"
    assert _parse_answer(q, "po") == "yes"
    # unmatched text is kept verbatim (trimmed)
    assert _parse_answer(q, "  pjesërisht ") == "pjesërisht"
    free = next(x for x in questions_for("civil") if x["key"] == "amount")
    assert _parse_answer(free, " 5000 € ") == "5000 €"
