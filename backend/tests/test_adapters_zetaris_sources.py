"""Zetaris federation tests: unit (no network) + integration (real platform).

The point of B1 is not that we can run SELECT 1 — it is that one question can
be answered from two different sources, and that each fragment keeps its own
URI. The unit tests pin that contract; the integration test proves it against
the running platform when it is reachable.
"""
import asyncio
import json
import os

import httpx
import pytest

from app.adapters.base import AdapterError, QuerySpec
from app.adapters.zetaris import ZetarisAdapter, ZetarisSource, parse_sources


def _adapter() -> ZetarisAdapter:
    return ZetarisAdapter(
        base_url="http://127.0.0.1:8888/api/v1.0",
        api_key="k",
        org_id="1",
        sources=[
            ZetarisSource(source="LIGJE", table="legal_corpus", title="doc_title", snippet="snippet"),
            ZetarisSource(source="PRAKTIKA", table="vendime", title="titull", snippet="tekst", page=None),
        ],
    )


def test_parse_sources_default_is_single_table():
    got = parse_sources("")
    assert len(got) == 1
    assert got[0].qualified == "legal_corpus"
    assert got[0].label == "corpus"


def test_parse_sources_json_roundtrip():
    raw = json.dumps([
        {"source": "LIGJE", "table": "legal_corpus", "title": "doc_title", "page": "page", "snippet": "snippet"},
        {"source": "PRAKTIKA", "table": "vendime", "title": "titull", "snippet": "tekst"},
    ])
    got = parse_sources(raw)
    assert [s.qualified for s in got] == ["LIGJE.legal_corpus", "PRAKTIKA.vendime"]
    assert got[1].page is None


def test_parse_sources_rejects_garbage():
    with pytest.raises(AdapterError):
        parse_sources("{not json")


def test_query_hits_every_source_and_keeps_uris(monkeypatch):
    adapter = _adapter()
    seen = []

    async def fake_sql(sql, limit=50):
        seen.append(sql)
        if "LIGJE." in sql:
            return [["Ligji i Punës", 55, "Punëdhënësi paguan pagën"]]
        return [["Vendimi nr. 120", "Gjykata e Apelit pranoi kërkesën"]]

    monkeypatch.setattr(adapter, "sql", fake_sql)
    ev = asyncio.run(adapter.query(QuerySpec(text="paga", limit=5)))

    assert len(seen) == 2, "one SQL statement per source"
    assert {e.source_id for e in ev} == {"LIGJE", "PRAKTIKA"}
    uris = [e.uri for e in ev]
    assert len(set(uris)) == 2 and all(u.startswith("zetaris://") for u in uris)
    ligje = next(e for e in ev if e.source_id == "LIGJE")
    assert ligje.page == 55
    assert ligje.meta["table"] == "LIGJE.legal_corpus"


def test_query_survives_one_dead_source(monkeypatch):
    adapter = _adapter()

    async def fake_sql(sql, limit=50):
        if "PRAKTIKA." in sql:
            raise AdapterError("zetaris: HTTP 500 boom")
        return [["Ligji i Punës", 55, "Paga"]]

    monkeypatch.setattr(adapter, "sql", fake_sql)
    ev = asyncio.run(adapter.query(QuerySpec(text="paga")))
    assert [e.source_id for e in ev] == ["LIGJE"]


def test_query_fails_closed_when_all_sources_fail(monkeypatch):
    adapter = _adapter()

    async def fake_sql(sql, limit=50):
        raise AdapterError("zetaris: HTTP 503")

    monkeypatch.setattr(adapter, "sql", fake_sql)
    with pytest.raises(AdapterError):
        asyncio.run(adapter.query(QuerySpec(text="paga")))


def test_query_filters_by_requested_source(monkeypatch):
    adapter = _adapter()
    seen = []

    async def fake_sql(sql, limit=50):
        seen.append(sql)
        return [["Vendimi", "tekst"]]

    monkeypatch.setattr(adapter, "sql", fake_sql)
    ev = asyncio.run(adapter.query(QuerySpec(text="paga", sources=["PRAKTIKA"])))
    assert len(seen) == 1 and "PRAKTIKA." in seen[0]
    assert ev[0].source_id == "PRAKTIKA"


def test_query_escapes_the_search_term(monkeypatch):
    adapter = _adapter()
    captured = {}

    async def fake_sql(sql, limit=50):
        captured["sql"] = sql
        return [["t", 1, "x"]]

    monkeypatch.setattr(adapter, "sql", fake_sql)
    asyncio.run(adapter.query(QuerySpec(text="O'Brien", sources=["LIGJE"])))
    assert "O''Brien" in captured["sql"]


# --- integration: the running platform, two real sources ---------------------

def _platform_up() -> bool:
    try:
        r = httpx.get("http://127.0.0.1:8888/api/v1.0/health", timeout=2)
        return r.status_code < 500
    except Exception:
        return False


@pytest.mark.skipif(os.environ.get("ZETARIS_LIVE") != "1", reason="set ZETARIS_LIVE=1 to query the local platform")
@pytest.mark.skipif(not _platform_up(), reason="local Zetaris platform not reachable")
def test_live_two_sources_one_question():
    adapter = ZetarisAdapter(
        sources=[
            ZetarisSource(source="NY_TAXI", table="customers", title="first_name", snippet="email", page=None),
            ZetarisSource(source="TPCDS_DB", table="reason", title="r_reason_desc", snippet="r_reason_desc", page=None),
        ]
    )
    ev = asyncio.run(adapter.query(QuerySpec(text="a", limit=4)))
    labels = {e.source_id for e in ev}
    assert labels == {"NY_TAXI", "TPCDS_DB"}, labels
    assert len({e.uri for e in ev}) == len(ev)
