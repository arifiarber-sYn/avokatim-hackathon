"""Local pseudonymization before external LLM calls (D-059 F1).

Parity with the German market standard (RA-MICRO JURA KI anonymizes locally
before anything reaches a model): personal data is replaced with stable
placeholders BEFORE the prompt leaves this machine, and the placeholders are
swapped back in the model's answer — including across streamed chunk
boundaries. The external provider only ever sees `[PERSON_1]`, `[EMAIL_1]`,
`[TEL_1]`, `[IBAN_1]`, `[ID_1]`.

Two detection layers:
1. Regex — emails, IBANs, phone numbers (date-like strings are excluded so
   procedural deadlines stay intact for the model).
2. Known terms — client/party names and ID numbers the calling service
   already knows from the matter file. They ride on a contextvar so the 20+
   provider call sites keep their signatures.

Legal citations (§ 573 BGB, "neni 176 i LPK", Aktenzeichen like VIII ZR
123/20) are deliberately NOT touched — the model needs them verbatim.
"""
import re
from contextvars import ContextVar

from app.llm.base import ChatMessage

# --- Known sensitive terms (set per request by services that know them) ----

_pii_terms: ContextVar[tuple[str, ...]] = ContextVar("pii_terms", default=())


def add_pii_terms(terms: list[str | None]) -> None:
    """Register names/IDs of the current request's people so the next LLM
    call replaces them. Additive within the request context; each ASGI
    request gets its own contextvar copy, so nothing leaks across requests."""
    cleaned = {t.strip() for t in terms if t and len(t.strip()) >= 3}
    if cleaned:
        _pii_terms.set(tuple(set(_pii_terms.get()) | cleaned))


def current_pii_terms() -> tuple[str, ...]:
    return _pii_terms.get()


# --- Regex layer ------------------------------------------------------------

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# DE22 5001 0517 5407 3249 31 and compact forms
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,3})?\b")
# +383 44 171 731 · 044/171-731 · 0176-1234567 — must start with + or 0.
# Law references ("08/L-022") never reach 7 digits before a letter breaks
# the run; dates are filtered separately below.
_PHONE_RE = re.compile(r"(?<![\w./-])(?:\+\d{1,3}[\s\-/.]?|0)\d(?:[\s\-/().]?\d){5,13}(?![\w-])")
_DATE_LIKE_RE = re.compile(r"^\d{1,2}[./]\d{1,2}[./]\d{2,4}$")

_KIND_EMAIL = "EMAIL"
_KIND_PHONE = "TEL"
_KIND_IBAN = "IBAN"
_KIND_PERSON = "PERSON"
_KIND_ID = "ID"

_PLACEHOLDER_RE = re.compile(r"\[(?:PERSON|EMAIL|TEL|IBAN|ID)_\d+\]")
# A '[' followed by what could still become a placeholder (stream holdback)
_PARTIAL_PLACEHOLDER_RE = re.compile(r"^\[[A-Z]{0,6}(?:_\d{0,5})?$")


class Pseudonymizer:
    """One instance per LLM call: builds the mapping while stripping the
    prompt, restores the model's answer with the same mapping."""

    def __init__(self, terms: tuple[str, ...] = ()):
        self._by_original: dict[str, str] = {}
        self._by_placeholder: dict[str, str] = {}
        self._counters: dict[str, int] = {}
        # Longest first so "Arben Krasniqi" wins over a bare "Arben"
        self._terms = sorted(terms, key=len, reverse=True)

    # -- strip ---------------------------------------------------------------

    def _placeholder(self, kind: str, original: str) -> str:
        existing = self._by_original.get(original)
        if existing:
            return existing
        self._counters[kind] = self._counters.get(kind, 0) + 1
        ph = f"[{kind}_{self._counters[kind]}]"
        self._by_original[original] = ph
        self._by_placeholder[ph] = original
        return ph

    def strip(self, text: str) -> str:
        if not text:
            return text
        # Known names/IDs first — they may contain digits the regexes would
        # otherwise carve up
        for term in self._terms:
            if term.lower() not in text.lower():
                continue
            kind = _KIND_ID if any(c.isdigit() for c in term) else _KIND_PERSON
            pattern = re.compile(
                r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE
            )
            # One placeholder per canonical term; the original casing of the
            # registered term is what restore() brings back
            text = pattern.sub(lambda _m, t=term, k=kind: self._placeholder(k, t), text)
        text = _EMAIL_RE.sub(lambda m: self._placeholder(_KIND_EMAIL, m.group()), text)
        text = _IBAN_RE.sub(lambda m: self._placeholder(_KIND_IBAN, m.group()), text)

        def _phone(m: re.Match) -> str:
            candidate = m.group()
            digits = sum(c.isdigit() for c in candidate)
            if digits < 7 or _DATE_LIKE_RE.match(candidate.strip()):
                return candidate
            return self._placeholder(_KIND_PHONE, candidate)

        return _PHONE_RE.sub(_phone, text)

    def strip_messages(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        return [ChatMessage(role=m.role, content=self.strip(m.content)) for m in messages]

    # -- restore ---------------------------------------------------------------

    @property
    def has_replacements(self) -> bool:
        return bool(self._by_placeholder)

    def restore(self, text: str) -> str:
        if not text or not self._by_placeholder:
            return text
        return _PLACEHOLDER_RE.sub(
            lambda m: self._by_placeholder.get(m.group(), m.group()), text
        )


def split_safe_emit(buffer: str) -> tuple[str, str]:
    """Split a streamed buffer into (safe-to-emit, holdback). The holdback is
    a trailing fragment that could still turn into a placeholder — e.g.
    '[PERSO' — and must wait for the next chunk before restoring."""
    i = buffer.rfind("[")
    if i == -1:
        return buffer, ""
    tail = buffer[i:]
    if "]" in tail:
        return buffer, ""
    if _PARTIAL_PLACEHOLDER_RE.match(tail):
        return buffer[:i], tail
    return buffer, ""
