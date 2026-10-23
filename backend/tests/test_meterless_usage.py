"""Meterless usage accounting (Open Agent B2): cost math + JSONL summary.

No network, no DB: every test works on a temporary file.
"""
import json
from pathlib import Path

from app.adapters.meterless import MeterlessAdapter, Usage, cost_of, summarize


def test_cost_is_zero_for_local_defaults():
    assert cost_of(1000, 500, 0.0, 0.0) == 0.0


def test_cost_from_prices_per_million():
    assert cost_of(1_000_000, 500_000, 0.5, 1.5) == 1.25


def test_adapter_defaults_to_free_local_prices(tmp_path):
    ad = MeterlessAdapter(base_url="http://127.0.0.1:9", usage_log=tmp_path / "u.jsonl")
    assert ad.price_in == 0.0
    assert ad.price_out == 0.0


def test_write_appends_one_json_line(tmp_path):
    ad = MeterlessAdapter(base_url="", usage_log=tmp_path / "u.jsonl")
    ad._write(Usage("j1", "local", 10, 20, 5, True, "now", cost_usd=0.0))
    ad._write(Usage("j2", "local", 1, 2, 3, False, "now2", cost_usd=0.000003))
    lines = (tmp_path / "u.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[1])["ok"] is False
    assert json.loads(lines[0])["cost_usd"] == 0.0


def test_summary_aggregates_and_counts_corrupt_lines(tmp_path):
    p = tmp_path / "u.jsonl"
    p.write_text(
        json.dumps(
            {
                "job_id": "a",
                "model": "local",
                "tokens_in": 100,
                "tokens_out": 50,
                "ms": 10,
                "ok": True,
                "ts": "t",
                "cost_usd": 0.0,
            }
        )
        + "\n{not json}\n"
        + json.dumps(
            {
                "job_id": "b",
                "model": "local",
                "tokens_in": 200,
                "tokens_out": 100,
                "ms": 30,
                "ok": False,
                "ts": "t",
                "cost_usd": 0.0001,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    s = summarize(p, last=5)
    assert s["calls"] == 2
    assert s["ok_calls"] == 1
    assert s["failed_calls"] == 1
    assert s["corrupt_lines"] == 1
    assert s["tokens_total"] == 450
    assert s["cost_usd"] == 0.0001
    assert s["ms_avg"] == 20
    assert len(s["last"]) == 2


def test_summary_missing_file_is_zero(tmp_path):
    s = summarize(tmp_path / "nope.jsonl")
    assert s["calls"] == 0
    assert s["cost_usd"] == 0.0
    assert s["last"] == []
