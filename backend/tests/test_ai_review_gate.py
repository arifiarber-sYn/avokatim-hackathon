"""Human-review gate for AI-generated documents (D-044, BRAK KI-Leitfaden)."""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.api.documents import require_ai_review
from app.models import Document


def _doc(**kw) -> Document:
    return Document(filename="draft.txt", mime_type="text/plain", **kw)


def test_plain_document_passes():
    require_ai_review(_doc(ai_generated=False))


def test_unreviewed_ai_document_is_blocked():
    with pytest.raises(HTTPException) as exc:
        require_ai_review(_doc(ai_generated=True, ai_reviewed_at=None))
    assert exc.value.status_code == 400


def test_reviewed_ai_document_passes():
    require_ai_review(
        _doc(ai_generated=True, ai_reviewed_at=datetime.now(UTC))
    )
