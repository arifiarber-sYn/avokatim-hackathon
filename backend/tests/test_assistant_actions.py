"""Assistant action execution with approval (D-053): route registration and
input validation. The heavy lifting (extraction, PDF filing, review gate) is
covered by test_deadline_suggest.py and test_ai_review_gate.py."""

import pytest
from pydantic import ValidationError

from app.api.assistant import ExtractActionsIn, SaveDraftIn, router


def _route_paths() -> set[str]:
    return {r.path for r in router.routes}


def test_action_routes_registered():
    paths = _route_paths()
    assert "/assistant/actions/extract-deadlines" in paths
    assert "/assistant/actions/save-draft" in paths


def test_extract_input_requires_text():
    import uuid

    with pytest.raises(ValidationError):
        ExtractActionsIn(matter_id=uuid.uuid4(), text="")
    ok = ExtractActionsIn(matter_id=uuid.uuid4(), text="Afati i ankesës është 15 ditë.")
    assert ok.text.startswith("Afati")


def test_save_draft_input_bounds():
    import uuid

    with pytest.raises(ValidationError):
        SaveDraftIn(matter_id=uuid.uuid4(), title="", content="x")
    with pytest.raises(ValidationError):
        SaveDraftIn(matter_id=uuid.uuid4(), title="t" * 201, content="x")
    ok = SaveDraftIn(matter_id=uuid.uuid4(), title="Draft ankese", content="Përmbajtja...")
    assert ok.title == "Draft ankese"
