"""Zetaris adapter: one query surface over fragmented legal sources.

The local Zetaris platform (docker: zetaris-api-1) exposes a REST SQL editor:

    POST {base}/sql-editor/sqls/run
    headers: Authorization: Bearer <key>, X-Org-ID: <id>, X-Request-ID: <uuid>
    body:    {"queryId": uuid, "sql": "...", "source": "SqlEditor", "limit": n}
    returns: {"data": [[...], ...]}

This module is the only place that knows that wire format. The rest of the
system sees Evidence, so the agent never depends on a sponsor SDK.

Federation (23.10.2026): one question can be answered from several registered
sources. Each source is described by a small declaration (catalog/schema, table,
which columns carry title/page/snippet), so adding a source is configuration,
not code. A dead source degrades the answer instead of silencing it; if every
source fails the adapter raises (fail-closed, no invented evidence).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.adapters.base import AdapterError, Evidence, QuerySpec, dedupe
from app.config import settings

logger = logging.getLogger(__name__)

VAULT_KEY = Path.home() / ".securevault" / "secrets" / "zetaris-api.key"


def _load_key() -> str:
    """Config first, then the vault file. The key never gets logged."""
    if settings.zetaris_api_key:
        return settings.zetaris_api_key
    if VAULT_KEY.exists():
        try:
            return VAULT_KEY.read_text(encoding="utf-8").strip()
        except OSError:  # pragma: no cover - unreadable vault
            return ""
    return ""


@dataclass(slots=True)
class ZetarisSource:
    """One federated source and the columns a citation needs.

    source is a registered datasource (tables queried as SOURCE.table); an
    empty value keeps the legacy plain table form.
    """

    source: str
    table: str
    title: str = "doc_title"
    snippet: str = "snippet"
    page: str | None = "page"

    @property
    def label(self) -> str:
        return self.source or "corpus"

    @property
    def qualified(self) -> str:
        return f"{self.source}.{self.table}" if self.source else self.table


def parse_sources(raw: str) -> list[ZetarisSource]:
    """Parse the operator JSON; an empty value keeps the single-table default."""
    raw = (raw or "").strip()
    if not raw:
        return [ZetarisSource(source="", table="legal_corpus")]
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"zetaris: zetaris_sources is not JSON ({exc})")
    out: list[ZetarisSource] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not item.get("table"):
            continue
        out.append(
            ZetarisSource(
                source=str(item.get("source") or ""),
                table=str(item["table"]),
                title=str(item.get("title") or "doc_title"),
                snippet=str(item.get("snippet") or "snippet"),
                page=(str(item["page"]) if item.get("page") else None),
            )
        )
    return out or [ZetarisSource(source="", table="legal_corpus")]


class ZetarisAdapter:
    name = "zetaris"

    def __init__(
        self,
        base_url: str | None = None,
        api_key=None,
        org_id: str | None = None,
        sources: list[ZetarisSource] | None = None,
    ) -> None:
        self.base_url = (base_url or settings.zetaris_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else _load_key()
        self.org_id = org_id or settings.zetaris_org_id
        self.sources = sources if sources is not None else parse_sources(settings.zetaris_sources)

    def available(self) -> bool:
        return bool(self.base_url and self.api_key)

    async def sql(self, sql: str, limit: int = 50) -> list[list[object]]:
        """Run one statement and return raw rows."""
        if not self.available():
            raise AdapterError("zetaris: base_url/api_key not configured")
        payload = {
            "queryId": str(uuid.uuid4()),
            "sql": sql,
            "source": "SqlEditor",
            "limit": limit,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Org-ID": str(self.org_id),
            "X-Request-ID": str(uuid.uuid4()),
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/sql-editor/sqls/run", json=payload, headers=headers
            )
        if resp.status_code >= 400:
            raise AdapterError(f"zetaris: HTTP {resp.status_code} {resp.text[:120]}")
        body = resp.json()
        rows = body.get("data") if isinstance(body, dict) else body
        if not isinstance(rows, list):
            raise AdapterError("zetaris: unexpected response shape")
        return rows

    async def query(self, spec: QuerySpec) -> list[Evidence]:
        """Search every configured source and return citable evidence.

        One question, several sources: every row keeps the source it came from
        and its own URI, so a merged answer can still point at the exact place
        the claim came from.
        """
        sources = self.sources
        if spec.sources:
            wanted = {str(x).lower() for x in spec.sources}
            sources = [
                src for src in sources
                if src.label.lower() in wanted or src.table.lower() in wanted
            ]
        if not sources:
            raise AdapterError("zetaris: no source matches the request")

        out: list[Evidence] = []
        errors: list[str] = []
        for src in sources:
            try:
                rows = await self.sql(self._sql_for(src, spec), limit=spec.limit)
            except AdapterError as exc:
                logger.warning("zetaris source %s failed: %s", src.qualified, exc)
                errors.append(f"{src.qualified}: {exc}")
                continue
            out.extend(self._to_evidence(src, rows))

        if not out and errors:
            raise AdapterError("zetaris: every source failed — " + "; ".join(errors[:3]))
        return dedupe(out)[: spec.limit]

    def _sql_for(self, src: ZetarisSource, spec: QuerySpec) -> str:
        term = spec.text.replace("'", "''")
        cols = [src.title, src.snippet]
        if src.page:
            cols.insert(1, src.page)
        return (
            f"SELECT {', '.join(cols)} FROM {src.qualified} "
            f"WHERE {src.snippet} ILIKE '%{term}%' OR {src.title} ILIKE '%{term}%' "
            f"LIMIT {int(spec.limit)}"
        )

    def _to_evidence(self, src: ZetarisSource, rows: list[list[object]]) -> list[Evidence]:
        out: list[Evidence] = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or not row:
                continue
            title = str(row[0]) if len(row) > 0 else src.label
            if src.page and len(row) > 2:
                page_raw = row[1]
                snippet = str(row[2])
            else:
                page_raw = None
                snippet = str(row[1]) if len(row) > 1 else json.dumps(row, ensure_ascii=False)
            uri = f"zetaris://{src.label}/" + hashlib.sha1(
                f"{src.qualified}|{title}|{page_raw}|{snippet}".encode("utf-8")
            ).hexdigest()[:16]
            out.append(
                Evidence(
                    source_id=src.label,
                    uri=uri,
                    fragment=snippet,
                    page=int(page_raw) if isinstance(page_raw, int) else None,
                    confidence=0.75,
                    meta={"title": title, "engine": "zetaris-local", "table": src.qualified},
                )
            )
        return out
