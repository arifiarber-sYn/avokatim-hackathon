"""Contract tests for the hackathon adapter layer.

These tests only exercise the new layer; they must pass without any network,
database or sponsor account.
"""
import asyncio
import json

import pytest

from app.adapters.base import AdapterError, Evidence, QuerySpec, dedupe
from app.adapters.meterless import MeterlessAdapter, Usage
from app.adapters.zetaris import FixtureAdapter, ZetarisAdapter


def test_evidence_roundtrip():
    ev = Evidence(source_id="ligje", uri="file:///a.pdf", fragment="Neni 12", page=3, confidence=0.9)
    assert ev.as_dict()["page"] == 3
    assert ev.as_dict()["source_id"] == "ligje"


def test_dedupe_keeps_first():
    a = Evidence(source_id="s", uri="u", fragment="tekst i njejte " * 10)
    b = Evidence(source_id="s", uri="u", fragment="tekst i njejte " * 10)
    c = Evidence(source_id="s", uri="u2", fragment="tjeter")
    assert len(dedupe([a, b, c])) == 2


def test_fixture_returns_two_sources(tmp_path):
    rows = [
        {"source_id": "ligje", "uri": "file:///ligj.pdf", "fragment": "Neni 12", "page": 4, "confidence": 0.8},
        {"source_id": "praktika", "uri": "file:///vendim.txt", "fragment": "Vendimi nr. 44", "confidence": 0.7},
    ]
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    adapter = FixtureAdapter(path=path)
    assert adapter.available()
    got = asyncio.run(adapter.query(QuerySpec(text="ndarje pasurie", limit=5)))
    assert {e.source_id for e in got} == {"ligje", "praktika"}
    assert all(e.meta.get("mock") is True for e in got)


def test_live_adapter_refuses_without_config():
    adapter = ZetarisAdapter(base_url="", api_key="")
    assert adapter.available() is False
    with pytest.raises(AdapterError):
        asyncio.run(adapter.query(QuerySpec(text="x")))


def test_meterless_usage_line(tmp_path):
    adapter = MeterlessAdapter(base_url="", usage_log=tmp_path / "usage.jsonl")
    assert adapter.available() is False
    record = Usage(job_id="j1", model="local", tokens_in=10, tokens_out=20, ms=5, ok=True, ts="now")
    adapter._write(record)
    line = (tmp_path / "usage.jsonl").read_text(encoding="utf-8").strip()
    assert json.loads(line)["tokens_out"] == 20
