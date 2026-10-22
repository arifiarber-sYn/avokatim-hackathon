"""Zetaris adapter: federated access to fragmented legal sources.

Zetaris keeps data where it lives (PDF corpus, practice notes, a demo SQL
registry) and exposes one query surface. This module is the only place that
knows the wire format; the rest of the system sees Evidence.

Two implementations ship together on purpose:

* ZetarisAdapter  - talks to the configured endpoint (live).
* FixtureAdapter  - deterministic fixture, used by tests and by the demo when
                    the live account is not reachable yet. It is always
                    labelled mock=True in meta so nobody mistakes it for live.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx

from app.adapters.base import AdapterError, Evidence, QuerySpec, dedupe
from app.config import settings

logger = logging.getLogger(__name__)


class ZetarisAdapter:
    name = "zetaris"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or settings.zetaris_base_url).rstrip("/")
        self.api_key = api_key or settings.zetaris_api_key

    def available(self) -> bool:
        return bool(self.base_url and self.api_key)

    async def query(self, spec: QuerySpec) -> list[Evidence]:
        if not self.available():
            raise AdapterError("zetaris: base_url/api_key not configured")
        payload = {
            "query": spec.text,
            "sources": list(spec.sources) or None,
            "limit": spec.limit,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{self.base_url}/v1/query", json=payload, headers=headers)
        if resp.status_code >= 400:
            raise AdapterError(f"zetaris: HTTP {resp.status_code}")
        return _parse_rows(resp.json(), spec.limit)


class FixtureAdapter:
    """Deterministic stand-in, clearly marked as mock."""

    name = "zetaris-fixture"

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path("data/evidence/zetaris-fixture.json")

    def available(self) -> bool:
        return self.path.exists()

    async def query(self, spec: QuerySpec) -> list[Evidence]:
        rows = json.loads(self.path.read_text(encoding="utf-8"))
        out: list[Evidence] = []
        for row in rows:
            meta = dict(row.get("meta") or {})
            meta["mock"] = True
            out.append(
                Evidence(
                    source_id=row["source_id"],
                    uri=row["uri"],
                    fragment=row["fragment"],
                    page=row.get("page"),
                    confidence=float(row.get("confidence", 0.5)),
                    meta=meta,
                )
            )
        return dedupe(out)[: spec.limit]


def _parse_rows(data: object, limit: int) -> list[Evidence]:
    rows = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise AdapterError("zetaris: unexpected response shape")
    out: list[Evidence] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        out.append(
            Evidence(
                source_id=str(row.get("source") or row.get("source_id") or "zetaris"),
                uri=str(row.get("uri") or row.get("url") or ""),
                fragment=str(row.get("fragment") or row.get("text") or ""),
                page=row.get("page"),
                confidence=float(row.get("score") or row.get("confidence") or 0.0),
                meta=dict(row.get("meta") or {}),
            )
        )
    return dedupe(out)[:limit]
