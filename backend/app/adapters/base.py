"""Contract shared by every external source adapter."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol, Sequence


class AdapterError(RuntimeError):
    """Raised when an adapter is selected but cannot serve a query."""


@dataclass(slots=True)
class Evidence:
    """One verifiable fragment returned by a source.

    uri and page are what the user clicks on: an answer is only as good as the
    place it points to.
    """

    source_id: str
    uri: str
    fragment: str
    page: int | None = None
    confidence: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QuerySpec:
    text: str
    sources: Sequence[str] = ()
    limit: int = 5


class SourceAdapter(Protocol):
    name: str

    def available(self) -> bool:
        """True when the adapter can actually answer right now."""

    async def query(self, spec: QuerySpec) -> list[Evidence]:
        """Return evidence for the spec, newest work only."""


def dedupe(evidence: Sequence[Evidence]) -> list[Evidence]:
    """Drop repeats: same source, same uri, same opening fragment."""
    seen: set[tuple[str, str, str]] = set()
    out: list[Evidence] = []
    for ev in evidence:
        key = (ev.source_id, ev.uri, (ev.fragment or "")[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
    return out
