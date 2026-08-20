"""Tests for the per-project health monitor (D-065). No network, no systemd."""
import importlib

rh = importlib.import_module("scripts.ops_roster_health")


def test_healthy_project_reports_ok(monkeypatch):
    monkeypatch.setattr(rh, "_svc_active", lambda n: True)
    monkeypatch.setattr(rh, "_http_up", lambda u: True if u else None)
    problems, repairs, ok, unresolved = rh.check()
    assert problems == []
    assert set(ok) == set(rh.PROJECTS)
    assert unresolved == []


def test_down_service_becomes_a_problem(monkeypatch):
    def svc(name):
        return name != "opshub.service"
    monkeypatch.setattr(rh, "_svc_active", svc)
    monkeypatch.setattr(rh, "_http_up", lambda u: True if u else None)
    monkeypatch.setattr(rh, "DO_REPAIR", False)
    problems, repairs, ok, unresolved = rh.check()
    assert any("OpsHub" in p and "opshub.service" in p for p in problems)
    assert "OpsHub" not in ok
    assert repairs == []
    assert "OpsHub" in unresolved  # repair not requested -> stays unresolved


def test_repair_only_touches_safe_projects(monkeypatch):
    # both a safe project (OpsHub) and the forbidden one (TotoTrading) are down
    def svc(name):
        return name not in ("opshub.service", "toto-trading.service")
    monkeypatch.setattr(rh, "_svc_active", svc)
    monkeypatch.setattr(rh, "_http_up", lambda u: True if u else None)
    monkeypatch.setattr(rh, "DO_REPAIR", True)
    restarted = []
    monkeypatch.setattr(rh, "_restart", lambda n: restarted.append(n) or True)
    problems, repairs, ok, unresolved = rh.check()
    # OpsHub (repairable) was restarted; TotoTrading (real money) never touched
    assert "opshub.service" in restarted
    assert "toto-trading.service" not in restarted
    assert any("TotoTrading" in p for p in problems)
    assert "OpsHub" not in unresolved  # self-healed after restart
    assert "TotoTrading" in unresolved  # never repairable


def test_report_shows_machine_line(monkeypatch):
    monkeypatch.setattr(rh, "_failed_units", lambda: [])
    monkeypatch.setattr(rh, "_disk_free_pct", lambda: 68)
    monkeypatch.setattr(rh, "_docker_count", lambda: 8)
    report = rh.build_report([], [], ["AvokatIM"], [])
    assert "✅" in report
    assert "disk 68% lirë" in report
    assert "docker 8 up" in report


def test_http_4xx_counts_as_up():
    # a 401/404 means the process answered -> up (not a 5xx / refused)
    assert rh._http_up(None) is None
