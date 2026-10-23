"""Feedback channel + citizen document templates: schema and data checks."""
import pytest
from jinja2 import Template
from pydantic import ValidationError

from app.api.feedback import FeedbackIn
from app.models.feedback import FEEDBACK_KINDS, FEEDBACK_STATUSES
from app.seeds.citizen_docs import CITIZEN_DOC_TEMPLATES

ALL_LOCALES = ["sq", "sr", "tr", "bs", "en", "zh"]
CATEGORIES = {"institucionet", "puna", "konsumatori", "te_pergjithshme", "noteria"}


def test_feedback_in_accepts_valid_payload():
    body = FeedbackIn(kind="ankese", name="Test", email="a@b.co", message="x" * 20)
    assert body.kind == "ankese"


def test_feedback_in_optional_identity():
    body = FeedbackIn(kind="sugjerim", message="një sugjerim i gjatë mjaftueshëm")
    assert body.name is None and body.email is None


def test_feedback_in_rejects_unknown_kind():
    with pytest.raises(ValidationError):
        FeedbackIn(kind="spam", message="x" * 20)


def test_feedback_in_rejects_short_message():
    with pytest.raises(ValidationError):
        FeedbackIn(kind="problem", message="shkurt")


def test_feedback_constants():
    assert FEEDBACK_KINDS == ["ankese", "sugjerim", "problem"]
    assert FEEDBACK_STATUSES == ["new", "handled"]


def test_templates_unique_with_valid_categories():
    codes = [tpl["code"] for tpl in CITIZEN_DOC_TEMPLATES]
    assert len(codes) == len(set(codes)) == 11  # 7 letters + 4 notary-pack drafts
    for tpl in CITIZEN_DOC_TEMPLATES:
        assert tpl["category"] in CATEGORIES, tpl["code"]


def test_templates_fully_localized_and_renderable():
    for tpl in CITIZEN_DOC_TEMPLATES:
        for locale in ALL_LOCALES:
            assert tpl["name"][locale], (tpl["code"], locale)
            for field in tpl["fields"]:
                assert field["label"][locale], (tpl["code"], field["key"], locale)
        values = {field["key"]: "test" for field in tpl["fields"]}
        values["date"] = "01.01.2026"
        rendered = Template(tpl["body_sq"]).render(**values)
        assert "{{" not in rendered and "}}" not in rendered, tpl["code"]
