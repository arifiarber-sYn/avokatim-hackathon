"""The simulation harnesses must never touch production by accident.

Regression test for the 2026-09-18 incident: full_simulation.py ran against the
live API, posted synthetic cases and fanned real "new case" mails out to ~14
lawyers before deleting the cases (reports/avokatim-rrjedha-emails-2026-09-18.md).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import sim_guard  # noqa: E402


def test_default_target_is_production(monkeypatch):
    monkeypatch.delenv("AVOKATIM_SIM_BASE_URL", raising=False)
    assert sim_guard.resolve_base() == sim_guard.PROD_BASE


def test_env_overrides_target(monkeypatch):
    monkeypatch.setenv("AVOKATIM_SIM_BASE_URL", "http://127.0.0.1:8001/api/")
    assert sim_guard.resolve_base() == "http://127.0.0.1:8001/api"


def test_production_is_refused_without_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["full_simulation.py"])
    with pytest.raises(SystemExit) as exc:
        sim_guard.assert_target_allowed(sim_guard.PROD_BASE, script="full_simulation.py")
    assert exc.value.code == 2


def test_production_allowed_with_explicit_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["full_simulation.py", "--allow-prod"])
    sim_guard.assert_target_allowed(sim_guard.PROD_BASE, script="full_simulation.py")


def test_test_instance_never_needs_the_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["full_simulation.py"])
    sim_guard.assert_target_allowed(
        "http://127.0.0.1:8001/api", script="full_simulation.py"
    )
