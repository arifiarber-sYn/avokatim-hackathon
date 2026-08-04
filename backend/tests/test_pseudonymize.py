"""D-059 F1: personal data must never reach an external LLM in clear text."""
import json

import pytest

from app.config import settings
from app.llm.base import ChatMessage, ChatResult, LLMProvider
from app.llm.pseudonymize import (
    Pseudonymizer,
    add_pii_terms,
    current_pii_terms,
    split_safe_emit,
)
from app.llm.router import PseudonymizingProvider, get_provider


def test_regex_layer_strips_email_phone_iban():
    p = Pseudonymizer()
    text = (
        "Klienti arben@example.com, tel +383 44 171 731, "
        "IBAN DE22 5001 0517 5407 3249 31, pagesa deri më 15.03.2026."
    )
    stripped = p.strip(text)
    assert "arben@example.com" not in stripped
    assert "44 171 731" not in stripped
    assert "5001 0517" not in stripped
    # Dates are procedural facts — they stay
    assert "15.03.2026" in stripped
    assert "[EMAIL_1]" in stripped
    assert "[TEL_1]" in stripped
    assert "[IBAN_1]" in stripped


def test_known_terms_albanian_and_german_names():
    p = Pseudonymizer(terms=("Arben Krasniqi", "Müller-Schmidt GmbH", "1234567890"))
    stripped = p.strip(
        "Paditësi Arben Krasniqi (nr. personal 1234567890) kundër Müller-Schmidt GmbH. "
        "arben krasniqi kërkon dëmshpërblim."
    )
    assert "Krasniqi" not in stripped
    assert "Müller" not in stripped
    assert "1234567890" not in stripped
    assert "[ID_1]" in stripped
    # Case-insensitive hits collapse into one placeholder; the roundtrip
    # brings back the canonical casing for both occurrences
    restored = p.restore(stripped)
    assert restored.count("Arben Krasniqi") == 2
    assert "Müller-Schmidt GmbH" in restored


def test_legal_citations_survive():
    p = Pseudonymizer()
    text = "Sipas § 573 BGB dhe vendimit VIII ZR 123/20; shih edhe nenin 176 të LPK (Ligji 03/L-006)."
    assert p.strip(text) == text


def test_restore_roundtrip():
    p = Pseudonymizer(terms=("Arben Krasniqi",))
    original = "Arben Krasniqi (arben@example.com, +383 44 171 731)"
    stripped = p.strip(original)
    assert "Arben" not in stripped and "@" not in stripped
    assert p.restore(stripped) == original


def test_json_output_stays_parseable():
    """extract_deadlines-style flows: model answers JSON containing our
    placeholders; after restore it must still parse."""
    p = Pseudonymizer(terms=("Arben Krasniqi",))
    p.strip("Klienti Arben Krasniqi, email arben@example.com")
    answer = '{"title": "Takim me [PERSON_1]", "contact": "[EMAIL_1]"}'
    restored = json.loads(p.restore(answer))
    assert restored["title"] == "Takim me Arben Krasniqi"
    assert restored["contact"] == "arben@example.com"


def test_split_safe_emit_holds_partial_placeholder():
    emit, hold = split_safe_emit("Sipas kontratës, [PERSO")
    assert emit == "Sipas kontratës, "
    assert hold == "[PERSO"
    # A complete bracket or plain text flows through
    assert split_safe_emit("me [PERSON_1] sot") == ("me [PERSON_1] sot", "")
    # '[' that can no longer become a placeholder is emitted
    assert split_safe_emit("lista [a") == ("lista [a", "")


def test_contextvar_terms_are_additive():
    add_pii_terms(["Arben Krasniqi", None, "  "])
    add_pii_terms(["Blerta Gashi"])
    terms = current_pii_terms()
    assert "Arben Krasniqi" in terms and "Blerta Gashi" in terms


class _EchoProvider(LLMProvider):
    """Fake external provider: records what it was sent, echoes it back."""

    name = "fake-external"

    def __init__(self):
        self.seen: list[str] = []

    async def chat(self, messages, *, temperature=0.3, max_tokens=None):
        self.seen.extend(m.content for m in messages)
        return ChatResult(content=messages[-1].content, provider=self.name, model="m")

    async def chat_stream(self, messages, *, temperature=0.3, max_tokens=None):
        self.seen.extend(m.content for m in messages)
        # Split the answer so a placeholder straddles two chunks
        text = messages[-1].content
        mid = text.find("_") + 1 if "_" in text else len(text) // 2
        yield ("delta", text[:mid])
        yield ("delta", text[mid:])

    def is_configured(self):
        return True


@pytest.mark.anyio
async def test_wrapper_hides_pii_from_provider_and_restores_answer():
    add_pii_terms(["Arben Krasniqi"])
    inner = _EchoProvider()
    wrapped = PseudonymizingProvider(inner)
    result = await wrapped.chat(
        [ChatMessage(role="user", content="Shkruaj email për Arben Krasniqi (arben@example.com)")]
    )
    assert all("Arben" not in s and "arben@" not in s for s in inner.seen)
    assert "Arben Krasniqi" in result.content
    assert "arben@example.com" in result.content


@pytest.mark.anyio
async def test_wrapper_restores_placeholder_split_across_stream_chunks():
    add_pii_terms(["Arben Krasniqi"])
    inner = _EchoProvider()
    wrapped = PseudonymizingProvider(inner)
    chunks = []
    async for kind, text in wrapped.chat_stream(
        [ChatMessage(role="user", content="Padia e Arben Krasniqi")]
    ):
        assert kind == "delta"
        chunks.append(text)
    full = "".join(chunks)
    assert "Arben Krasniqi" in full
    assert "[PERSON" not in full


def test_router_wraps_external_but_never_local(monkeypatch):
    monkeypatch.setattr(settings, "llm_pseudonymize", True)
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")
    external = get_provider("deepseek")
    assert isinstance(external, PseudonymizingProvider)
    assert external.name == "deepseek"  # callers still log the real name

    monkeypatch.setattr(settings, "local_llm_model", "some-model")
    local = get_provider("local")
    assert not isinstance(local, PseudonymizingProvider)

    monkeypatch.setattr(settings, "llm_pseudonymize", False)
    assert not isinstance(get_provider("deepseek"), PseudonymizingProvider)
