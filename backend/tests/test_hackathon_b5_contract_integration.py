"""B5 — contract, integration and regression tests for the hackathon layer.

The 24.10 plan step B5 asks for at least fifteen new tests across three
classes. Everything here runs offline: the Zetaris platform and the Meterless
hotspot are replaced by captured doubles, so the suite proves the *contract*
(what an adapter must return, what it must refuse) without needing the live
sponsors. The existing tests stay untouched; this file only adds coverage.

Groups:
  * contract     — Evidence/QuerySpec/dedupe invariants that every adapter shares
  * zetaris      — parsing, SQL shape, row mapping, filtering, limit, degradation
  * meterless    — cost math, usage log, summary window, chat success/failure
  * integration  — two adapters and two federated sources behind one contract
"""
from __future__ import annotations

import asyncio
import json

import pytest

from app.adapters import meterless as meterless_mod
from app.adapters.base import AdapterError, Evidence, QuerySpec, dedupe
from app.adapters.meterless import MeterlessAdapter, Usage, cost_of, summarize
from app.adapters.zetaris import ZetarisAdapter, ZetarisSource, parse_sources


def _zetaris(*sources: ZetarisSource) -> ZetarisAdapter:
    return ZetarisAdapter(
        base_url="http://127.0.0.1:8888/api/v1.0",
        api_key="k",
        org_id="1",
        sources=list(sources) or [ZetarisSource(source="LIGJE", table="legal_corpus")],
    )


def _run(coro):
    return asyncio.run(coro)


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = json.dumps(self._payload)

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    """Minimal stand-in for httpx.AsyncClient used by MeterlessAdapter.chat."""

    last_url: str | None = None
    last_payload: dict | None = None
    response: _FakeResponse = _FakeResponse(200, {})

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None):
        type(self).last_url = url
        type(self).last_payload = json
        return type(self).response


# contract: what every adapter promises
def test_queryspec_defaults_fire_no_sources_and_five_hits():
    spec = QuerySpec("a mund të kërkoj ndarje pasuria")
    assert spec.sources == ()
    assert spec.limit == 5


def test_evidence_meta_is_per_instance_not_shared():
    first = Evidence(source_id="a", uri="u1", fragment="f1")
    second = Evidence(source_id="b", uri="u2", fragment="f2")
    first.meta["seen"] = True
    assert second.meta == {}
    assert first.confidence == 0.0 and second.page is None


def test_dedupe_compares_only_first_eighty_fragment_chars():
    stem = "x" * 80
    a = Evidence(source_id="s", uri="u", fragment=stem + "A")
    b = Evidence(source_id="s", uri="u", fragment=stem + "B")
    assert len(dedupe([a, b])) == 1


def test_dedupe_keeps_same_uri_from_different_sources():
    a = Evidence(source_id="LIGJE", uri="u", fragment="f")
    b = Evidence(source_id="PRAKTIKA", uri="u", fragment="f")
    assert len(dedupe([a, b])) == 2


def test_dedupe_preserves_input_order():
    a = Evidence(source_id="s", uri="u1", fragment="f")
    b = Evidence(source_id="s", uri="u2", fragment="f")
    c = Evidence(source_id="s", uri="u3", fragment="f")
    assert [e.uri for e in dedupe([c, a, b, c])] == ["u3", "u1", "u2"]


# zetaris: declaration parsing
def test_parse_sources_skips_bad_items_but_keeps_good_one():
    raw = json.dumps([{"source": "X"}, {"table": "vendime"}, "junk", {"table": ""}])
    got = parse_sources(raw)
    assert [s.qualified for s in got] == ["vendime"]


def test_parse_sources_non_list_json_falls_back_to_default():
    got = parse_sources(json.dumps({"table": "legal_corpus"}))
    assert len(got) == 1
    assert got[0].qualified == "legal_corpus"


def test_parse_sources_keeps_legacy_label_when_source_is_empty():
    assert ZetarisSource(source="", table="t").label == "corpus"


def test_parse_sources_rejects_broken_json_as_adapter_error():
    with pytest.raises(AdapterError):
        parse_sources("[{]")


# zetaris: SQL + row mapping
def test_sql_for_orders_columns_and_doubles_quotes():
    src = ZetarisSource(source="LIGJE", table="legal_corpus", title="doc_title",
                        page="page", snippet="snippet")
    sql = _zetaris(src)._sql_for(src, QuerySpec(text="O'Brien", limit=7))
    assert sql.startswith("SELECT doc_title, page, snippet FROM LIGJE.legal_corpus ")
    assert "ILIKE '%O''Brien%'" in sql
    assert sql.endswith("LIMIT 7")


def test_sql_for_omits_page_column_when_source_has_none():
    src = ZetarisSource(source="PRAKTIKA", table="vendime", title="titull",
                        snippet="tekst", page=None)
    sql = _zetaris(src)._sql_for(src, QuerySpec(text="ndarje", limit=3))
    assert sql.startswith("SELECT titull, tekst FROM PRAKTIKA.vendime ")
    assert "LIMIT 3" in sql


def test_to_evidence_without_page_column_sets_page_none():
    src = ZetarisSource(source="PRAKTIKA", table="vendime", title="titull",
                        snippet="tekst", page=None)
    out = _zetaris(src)._to_evidence(src, [["Vendimi A", "teksti i fragmentit"]])
    assert len(out) == 1
    ev = out[0]
    assert (ev.source_id, ev.page, ev.fragment) == ("PRAKTIKA", None, "teksti i fragmentit")
    assert ev.meta["title"] == "Vendimi A"
    assert ev.meta["table"] == "PRAKTIKA.vendime"
    assert ev.uri.startswith("zetaris://PRAKTIKA/")
    assert ev.confidence == 0.75


def test_to_evidence_with_page_column_keeps_int_page():
    src = ZetarisSource(source="LIGJE", table="legal_corpus", title="doc_title",
                        page="page", snippet="snippet")
    ev = _zetaris(src)._to_evidence(src, [["Ligji", 55, "Neni 12"]])[0]
    assert ev.page == 55
    assert ev.fragment == "Neni 12"


def test_to_evidence_uri_is_stable_and_content_bound():
    src = ZetarisSource(source="LIGJE", table="legal_corpus")
    adapter = _zetaris(src)
    row = ["Ligji", 12, "Neni 1"]
    assert adapter._to_evidence(src, [row])[0].uri == adapter._to_evidence(src, [row])[0].uri
    changed = ["Ligji", 12, "Neni 2"]
    assert adapter._to_evidence(src, [row])[0].uri != adapter._to_evidence(src, [changed])[0].uri


def test_to_evidence_skips_non_row_payloads():
    src = ZetarisSource(source="LIGJE", table="legal_corpus")
    assert _zetaris(src)._to_evidence(src, [[], "junk", {"a": 1}, None]) == []


# zetaris: query behaviour (offline doubles)
def test_query_respects_limit_after_mapping(monkeypatch):
    src = ZetarisSource(source="LIGJE", table="legal_corpus")
    adapter = _zetaris(src)

    async def fake_sql(sql, limit=50):
        return [[f"Ligji {i}", 1, f"fragment {i}"] for i in range(6)]

    monkeypatch.setattr(adapter, "sql", fake_sql)
    got = _run(adapter.query(QuerySpec(text="paga", limit=2)))
    assert [e.meta["title"] for e in got] == ["Ligji 0", "Ligji 1"]


def test_query_source_filter_is_case_insensitive_by_table(monkeypatch):
    adapter = _zetaris(
        ZetarisSource(source="LIGJE", table="legal_corpus"),
        ZetarisSource(source="PRAKTIKA", table="vendime"),
    )
    seen: list[str] = []

    async def fake_sql(sql, limit=50):
        seen.append(sql)
        return [["t", 1, "f"]]

    monkeypatch.setattr(adapter, "sql", fake_sql)
    got = _run(adapter.query(QuerySpec(text="x", sources=["legal_corpus"])))
    assert len(seen) == 1 and "LIGJE.legal_corpus" in seen[0]
    assert {e.source_id for e in got} == {"LIGJE"}


def test_query_unknown_source_raises_before_any_sql(monkeypatch):
    adapter = _zetaris(ZetarisSource(source="LIGJE", table="legal_corpus"))
    calls: list[str] = []

    async def fake_sql(sql, limit=50):
        calls.append(sql)
        return [["t", 1, "f"]]

    monkeypatch.setattr(adapter, "sql", fake_sql)
    with pytest.raises(AdapterError, match="no source matches"):
        _run(adapter.query(QuerySpec(text="x", sources=["askush"])))
    assert calls == []


def test_query_empty_hits_are_not_an_error(monkeypatch):
    adapter = _zetaris(ZetarisSource(source="LIGJE", table="legal_corpus"))

    async def fake_sql(sql, limit=50):
        return []

    monkeypatch.setattr(adapter, "sql", fake_sql)
    assert _run(adapter.query(QuerySpec(text="asnjë hit"))) == []


def test_query_fails_closed_with_every_source_error(monkeypatch):
    adapter = _zetaris(
        ZetarisSource(source="LIGJE", table="legal_corpus"),
        ZetarisSource(source="PRAKTIKA", table="vendime"),
    )

    async def fake_sql(sql, limit=50):
        raise AdapterError("down")

    monkeypatch.setattr(adapter, "sql", fake_sql)
    with pytest.raises(AdapterError, match="every source failed"):
        _run(adapter.query(QuerySpec(text="x")))


# meterless: cost + usage log
def test_cost_is_linear_in_tokens_and_prices():
    assert cost_of(2_000_000, 1_000_000, 1.0, 2.0) == 4.0
    assert cost_of(1, 1, 0.0, 0.0) == 0.0


def test_usage_as_dict_has_default_zero_cost_and_all_fields():
    record = Usage(job_id="j", model="local", tokens_in=1, tokens_out=2, ms=3, ok=True, ts="t")
    data = record.as_dict()
    assert data["cost_usd"] == 0.0
    assert set(data) == {"job_id", "model", "tokens_in", "tokens_out", "ms", "ok", "ts", "cost_usd"}


def test_usage_log_appends_and_stays_parseable(tmp_path):
    adapter = MeterlessAdapter(base_url="", usage_log=tmp_path / "u.jsonl")
    adapter._write(Usage("a", "local", 1, 2, 3, True, "t1"))
    adapter._write(Usage("b", "local", 4, 5, 6, False, "t2"))
    lines = (tmp_path / "u.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["job_id"] for line in lines] == ["a", "b"]


def test_summary_last_window_and_average(tmp_path):
    path = tmp_path / "u.jsonl"
    rows = [
        {"job_id": "a", "model": "local", "ms": 10, "ok": True},
        {"job_id": "b", "model": "local", "ms": 20, "ok": True},
        {"job_id": "c", "model": "other", "ms": 30, "ok": False},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    summary = summarize(path, last=2)
    assert summary["ms_avg"] == 20
    assert [r["job_id"] for r in summary["last"]] == ["b", "c"]
    assert [r["job_id"] for r in summarize(path, last=0)["last"]] == ["c"]
    assert summary["by_model"] == {"local": 2, "other": 1}


def test_summary_tolerates_missing_and_string_cost_fields(tmp_path):
    path = tmp_path / "u.jsonl"
    path.write_text(
        json.dumps({"job_id": "a", "ok": True, "cost_usd": "0.5"}) + "\n"
        + json.dumps({"job_id": "b", "ok": False}) + "\n",
        encoding="utf-8",
    )
    summary = summarize(path)
    assert summary["cost_usd"] == 0.5
    assert summary["by_model"] == {"?": 2}
    assert summary["calls"] == 2 and summary["failed_calls"] == 1


def test_summary_empty_file_is_all_zero(tmp_path):
    path = tmp_path / "u.jsonl"
    path.write_text("\n\n", encoding="utf-8")
    summary = summarize(path)
    assert (summary["calls"], summary["tokens_total"], summary["ms_avg"], summary["last"]) == (0, 0, 0, [])


# meterless: chat path (httpx double)
def test_chat_success_writes_priced_usage_line(tmp_path, monkeypatch):
    _FakeClient.response = _FakeResponse(
        200,
        {
            "choices": [{"message": {"content": "Përgjigje lokale"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20},
        },
    )
    monkeypatch.setattr(meterless_mod.httpx, "AsyncClient", _FakeClient)
    log = tmp_path / "usage.jsonl"
    adapter = MeterlessAdapter(
        base_url="http://127.0.0.1:9", usage_log=log, price_in=1.0, price_out=2.0
    )
    text, record = _run(adapter.chat("Përshëndetje", model="qwen-local"))
    assert text == "Përgjigje lokale"
    assert record.ok is True and record.model == "qwen-local"
    assert record.tokens_in == 100 and record.tokens_out == 20
    assert record.cost_usd == 0.00014
    assert _FakeClient.last_url.endswith("/v1/chat/completions")
    assert _FakeClient.last_payload["messages"][0]["content"] == "Përshëndetje"
    line = json.loads(log.read_text(encoding="utf-8").strip())
    assert line["cost_usd"] == 0.00014
    assert line["job_id"].startswith("ml-")


def test_chat_failure_logs_failed_call_then_raises(tmp_path, monkeypatch):
    _FakeClient.response = _FakeResponse(503, {"error": "down"})
    monkeypatch.setattr(meterless_mod.httpx, "AsyncClient", _FakeClient)
    log = tmp_path / "usage.jsonl"
    adapter = MeterlessAdapter(base_url="http://127.0.0.1:9", usage_log=log)
    with pytest.raises(AdapterError, match="HTTP 503"):
        _run(adapter.chat("x"))
    line = json.loads(log.read_text(encoding="utf-8").strip())
    assert line["ok"] is False
    assert (line["tokens_in"], line["tokens_out"], line["cost_usd"]) == (0, 0, 0.0)


def test_chat_without_base_url_raises_and_writes_nothing(tmp_path, monkeypatch):
    _FakeClient.response = _FakeResponse(200, {})
    monkeypatch.setattr(meterless_mod.httpx, "AsyncClient", _FakeClient)
    log = tmp_path / "usage.jsonl"
    adapter = MeterlessAdapter(base_url="", usage_log=log)
    with pytest.raises(AdapterError, match="base_url not configured"):
        _run(adapter.chat("x"))
    assert log.exists() is False


# integration: two adapters + two federated sources, one contract
def test_two_adapters_serialize_into_one_json_contract():
    ev = Evidence(source_id="LIGJE", uri="zetaris://LIGJE/abc", fragment="Neni 12", page=3)
    usage = Usage("ml-1", "local", 10, 5, 80, True, "2026-10-24T12:00:00+00:00", 0.0)
    payload = {"evidence": ev.as_dict(), "usage": usage.as_dict()}
    restored = json.loads(json.dumps(payload))
    assert restored["evidence"]["uri"].startswith("zetaris://")
    assert restored["usage"]["ms"] == 80


def test_federation_merges_two_sources_with_distinct_uris(monkeypatch):
    adapter = _zetaris(
        ZetarisSource(source="LIGJE", table="legal_corpus"),
        ZetarisSource(source="PRAKTIKA", table="vendime", title="titull", snippet="tekst", page=None),
    )

    async def fake_sql(sql, limit=50):
        if "LIGJE." in sql:
            return [["Ligji i Punës", 55, "Neni 12 — pushimi vjetor"]]
        return [["Vendimi 44/2024", "Gjykata njohu të drejtën"]]

    monkeypatch.setattr(adapter, "sql", fake_sql)
    got = _run(adapter.query(QuerySpec(text="pushim vjetor", limit=5)))
    assert len(got) == 2
    assert {e.source_id for e in got} == {"LIGJE", "PRAKTIKA"}
    assert len({e.uri for e in got}) == 2
    assert all(e.confidence == 0.75 and e.fragment for e in got)
