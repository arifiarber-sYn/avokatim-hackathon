"""Contract tests for the hackathon adapter layer (no network, no DB)."""
import asyncio
import json

import pytest

from app.adapters.base import AdapterError, Evidence, QuerySpec, dedupe
from app.adapters.meterless import MeterlessAdapter, Usage
from app.adapters.zetaris import ZetarisAdapter


def test_evidence_roundtrip():
    ev = Evidence(source_id="ligje", uri="file:///a.pdf", fragment="Neni 12", page=3, confidence=0.9)
    assert ev.as_dict()["page"] == 3
    assert ev.as_dict()["source_id"] == "ligje"


def test_dedupe_keeps_first():
    a = Evidence(source_id="s", uri="u", fragment="tekst i njejte " * 10)
    b = Evidence(source_id="s", uri="u", fragment="tekst i njejte " * 10)
    c = Evidence(source_id="s", uri="u2", fragment="tjeter")
    assert len(dedupe([a, b, c])) == 2


def test_zetaris_refuses_without_key():
    adapter = ZetarisAdapter(base_url="http://127.0.0.1:9/api", api_key="", org_id="1")
    assert adapter.available() is False
    with pytest.raises(AdapterError):
        asyncio.run(adapter.sql("SELECT 1"))


def test_zetaris_available_with_config():
    adapter = ZetarisAdapter(base_url="http://127.0.0.1:8888/api/v1.0", api_key="k", org_id="1")
    assert adapter.available() is True
    assert adapter.org_id == "1"


def test_meterless_usage_line(tmp_path):
    adapter = MeterlessAdapter(base_url="", usage_log=tmp_path / "usage.jsonl")
    assert adapter.available() is False
    record = Usage(job_id="j1", model="local", tokens_in=10, tokens_out=20, ms=5, ok=True, ts="now")
    adapter._write(record)
    line = (tmp_path / "usage.jsonl").read_text(encoding="utf-8").strip()
    assert json.loads(line)["tokens_out"] == 20

