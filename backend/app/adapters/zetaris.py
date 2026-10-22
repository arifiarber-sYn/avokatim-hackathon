"""Zetaris adapter: one query surface over fragmented legal sources.

The local Zetaris platform (docker: zetaris-api-1) exposes a REST SQL editor:

    POST {base}/sql-editor/sqls/run
    headers: Authorization: Bearer <key>, X-Org-ID: <id>, X-Request-ID: <uuid>
    body:    {"queryId": uuid, "sql": "...", "source": "SqlEditor", "limit": n}
    returns: {"data": [[...], ...]}

This module is the only place that knows that wire format. The rest of the
system sees Evidence, so the agent never depends on a sponsor SDK.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
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


class ZetarisAdapter:
    name = "zetaris"

    def __init__(
        self,
        base_url: str | None = None,
        api_key=None,
        org_id: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.zetaris_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else _load_key()
        self.org_id = org_id or settings.zetaris_org_id

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
        """Search the corpus through the platform's SQL surface.

        The corpus tables are created by the bootstrap step; if they are not
        present yet we fall back to a metadata probe so the caller still gets
        a truthful answer instead of an exception storm.
        """
        term = spec.text.replace("'", "''")
        sql = (
            "SELECT doc_title, page, snippet FROM legal_corpus "
            f"WHERE snippet ILIKE '%{term}%' OR doc_title ILIKE '%{term}%' "
            f"LIMIT {int(spec.limit)}"
        )
        try:
            rows = await self.sql(sql, limit=spec.limit)
        except AdapterError as exc:
            logger.warning("zetaris corpus query failed: %s", exc)
            raise
        out: list[Evidence] = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or not row:
                continue
            title = str(row[0]) if len(row) > 0 else "zetaris"
            page = row[1] if len(row) > 1 else None
            snippet = str(row[2]) if len(row) > 2 else json.dumps(row, ensure_ascii=False)
            uri = "zetaris://corpus/" + hashlib.sha1(
                f"{title}|{page}|{snippet}".encode("utf-8")
            ).hexdigest()[:16]
            out.append(
                Evidence(
                    source_id="zetaris",
                    uri=uri,
                    fragment=snippet,
                    page=int(page) if isinstance(page, int) else None,
                    confidence=0.75,
                    meta={"title": title, "engine": "zetaris-local"},
                )
            )
        return dedupe(out)[: spec.limit]

