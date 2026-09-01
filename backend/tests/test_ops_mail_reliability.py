"""D-063: the mail pipeline must never lose correspondence silently.

Covers the three holes the Vuksani incident exposed, plus XK↔DE parity of
inbound handling (both campaigns share one inbox and one triage):

1. last_uid must not advance past unreported human mail when the per-run cap
   is hit (the old code lost backlog overflow forever).
2. Every operator send lands in the replies ledger (data/ops/replies_log.csv).
3. The LLM-free watchdog detects stale mail and cron failure streaks.
4. Parity: XK lawyer reply -> "human" (autonomous), DE company reply ->
   "company" (PO/JO escalation), STOP -> "optout" — same inbox, same rules.
"""
import importlib.util
import json
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


triage = _load("ops_inbox_triage")
watchdog = _load("ops_watchdog")
send_reply = _load("ops_send_reply")


# --- parity: one inbox, two campaigns, same classification rules -------------

COMPANY_DOMAINS = {"stp.one": "Septeo", "advocard.de": "ADVOCARD"}


def test_parity_xk_lawyer_reply_is_human():
    kind = triage._classify(
        "Av. Katarina Vuksani <katarinavuksani@hotmail.com>",
        "Re: AvokatIM — zyra juaj digjitale",
        "Faleminderit, por s'po mundem me e hap faqen nga telefoni. Si të regjistrohem?",
        COMPANY_DOMAINS,
    )
    assert kind == "human"


def test_parity_de_company_reply_is_company_never_human():
    kind = triage._classify(
        "M&A Team <corporate@stp.one>",
        "Re: AI-native legal platform",
        "Thanks, we would like to schedule a call.",
        COMPANY_DOMAINS,
    )
    assert kind == "company"


def test_parity_stop_is_optout_in_both_languages():
    for frm, subj in [
        ("avokat@example-ks.com", "STOP"),
        ("kanzlei@example.de", "Bitte abbestellen"),
    ]:
        assert triage._classify(frm, subj, "", COMPANY_DOMAINS) == "optout"


def test_parity_company_stop_still_escalates_to_owner():
    # Even a terse "stop" from a target company is an M&A signal the owner
    # must see — company outranks optout.
    kind = triage._classify("info@advocard.de", "STOP", "", COMPANY_DOMAINS)
    assert kind == "company"


# --- fix: capped runs must not skip mail --------------------------------------

class FakeIMAP:
    """Enough of imaplib for run(): a mailbox of raw RFC822 messages by UID."""

    def __init__(self, messages: dict[int, bytes]):
        self.messages = messages

    def login(self, *_): return ("OK", [])

    def select(self, *_, **__): return ("OK", [b"1"])

    def uid(self, cmd, *args):
        if cmd == "SEARCH":
            query = args[-1]  # ("SEARCH", None, "UID 101:*")
            uids = sorted(self.messages)
            if query.startswith("UID "):
                start = int(query.split()[1].split(":")[0])
                uids = [u for u in uids if u >= start] or uids[-1:]
            return ("OK", [" ".join(map(str, uids)).encode()])
        if cmd == "FETCH":
            uid = int(args[0])  # ("FETCH", "101", "(BODY.PEEK[])")
            return ("OK", [(b"", self.messages[uid])])
        raise AssertionError(cmd)

    def logout(self): return ("BYE", [])


def _mail(sender: str, subject: str, body: str = "hello") -> bytes:
    return (f"From: {sender}\r\nTo: ops@avokatiim.ai\r\nSubject: {subject}\r\n"
            f"Date: Tue, 04 Aug 2026 13:42:00 +0200\r\n"
            f"Message-ID: <{abs(hash((sender, subject)))}@x>\r\n\r\n{body}\r\n").encode()


@pytest.fixture
def inbox_env(tmp_path, monkeypatch):
    monkeypatch.setattr(triage, "STATE_FILE", tmp_path / "inbox_state.json")
    monkeypatch.setattr(triage, "SUPPRESS_LEDGER", tmp_path / "suppress.txt")
    monkeypatch.setattr(triage, "COMPANIES_CSV", tmp_path / "none.csv")
    monkeypatch.setattr(triage, "COMPANY_REPLIES", tmp_path / "replies.txt")
    monkeypatch.setattr(triage.settings, "imap_host", "imap.test", raising=False)
    monkeypatch.setattr(triage.settings, "imap_user", "ops@test", raising=False)
    monkeypatch.setattr(triage.settings, "imap_password", "x", raising=False)


def test_capped_run_does_not_lose_backlog(inbox_env, monkeypatch):
    # 15 human mails arrive after UID 100 while the pipeline was down.
    messages = {100 + i: _mail(f"person{i}@ex.com", f"Pyetje {i}") for i in range(1, 16)}
    monkeypatch.setattr(triage.imaplib, "IMAP4_SSL", lambda *a, **k: FakeIMAP(messages))
    triage._save_state({"last_uid": 100})

    first = triage.run()
    assert len(first["human"]) == triage.MAX_HUMAN_PER_RUN
    assert first["truncated"] is True
    # State stops at the last REPORTED mail, not at max(uids).
    assert triage._load_state()["last_uid"] == 110

    second = triage.run()
    assert [m["uid"] for m in second["human"]] == list(range(111, 116))
    assert "truncated" not in second
    assert triage._load_state()["last_uid"] == 115


def test_uncapped_run_advances_normally(inbox_env, monkeypatch):
    # First subject carries a raw 8-bit char — a malformed header must be
    # tolerated, not crash the run (found by this very test).
    messages = {201: _mail("a@ex.com", "Një pyetje"), 202: _mail("b@ex.com", "Dy")}
    monkeypatch.setattr(triage.imaplib, "IMAP4_SSL", lambda *a, **k: FakeIMAP(messages))
    triage._save_state({"last_uid": 200})
    report = triage.run()
    assert len(report["human"]) == 2
    assert triage._load_state()["last_uid"] == 202


# --- correspondence ledger ------------------------------------------------------

def test_every_send_lands_in_replies_log(tmp_path, monkeypatch):
    monkeypatch.setattr(send_reply, "REPLIES_LOG", tmp_path / "replies_log.csv")
    send_reply._log_send("a@ex.com", "Re: pyetja", "trupi i emailit", 0)
    send_reply._log_send("b@ex.com", "Oferta", "tjetër", 2)
    lines = (tmp_path / "replies_log.csv").read_text().strip().splitlines()
    assert lines[0].startswith("sent_at,to,subject")
    assert len(lines) == 3
    assert "a@ex.com" in lines[1] and "b@ex.com" in lines[2]


# --- watchdog -------------------------------------------------------------------

def test_watchdog_flags_stale_unprocessed_mail(tmp_path, monkeypatch):
    state = tmp_path / "inbox_state.json"
    state.write_text(json.dumps({"last_uid": 100}))
    monkeypatch.setattr(watchdog, "INBOX_STATE", state)
    old = (datetime.now(UTC) - timedelta(hours=2)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    messages = {101: f"Date: {old}\r\n\r\nx".encode()}

    monkeypatch.setattr(watchdog.imaplib, "IMAP4_SSL", lambda *a, **k: FakeIMAP(messages))
    monkeypatch.setattr(watchdog.settings, "imap_host", "imap.test", raising=False)
    monkeypatch.setattr(watchdog.settings, "imap_user", "ops@test", raising=False)
    monkeypatch.setattr(watchdog.settings, "imap_password", "x", raising=False)
    problem = watchdog.check_stale_mail()
    assert problem and "papërpunuar" in problem


def test_watchdog_flags_cron_error_streak(tmp_path, monkeypatch):
    db_path = tmp_path / "openclaw.sqlite"
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE cron_jobs (job_id TEXT, name TEXT)")
    db.execute("CREATE TABLE cron_run_receipts (job_id TEXT, status TEXT, error_text TEXT, started_at_ms INTEGER)")
    db.execute("INSERT INTO cron_jobs VALUES ('j1', ?)", (watchdog.TRIAGE_JOB_NAME,))
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    for i in range(watchdog.ERROR_STREAK):
        db.execute("INSERT INTO cron_run_receipts VALUES ('j1', 'error', 'model idle timeout', ?)",
                   (now_ms - i * 600_000,))
    db.commit(); db.close()
    monkeypatch.setattr(watchdog, "OPENCLAW_DB", db_path)
    problem = watchdog.check_cron_errors()
    assert problem and "dështime radhazi" in problem


def test_watchdog_quiet_after_recovery(tmp_path, monkeypatch):
    db_path = tmp_path / "openclaw.sqlite"
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE cron_jobs (job_id TEXT, name TEXT)")
    db.execute("CREATE TABLE cron_run_receipts (job_id TEXT, status TEXT, error_text TEXT, started_at_ms INTEGER)")
    db.execute("INSERT INTO cron_jobs VALUES ('j1', ?)", (watchdog.TRIAGE_JOB_NAME,))
    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    # newest run OK, older ones failed — streak broken, no alarm
    db.execute("INSERT INTO cron_run_receipts VALUES ('j1', 'ok', NULL, ?)", (now_ms,))
    for i in range(1, watchdog.ERROR_STREAK + 1):
        db.execute("INSERT INTO cron_run_receipts VALUES ('j1', 'error', 'x', ?)",
                   (now_ms - i * 600_000,))
    db.commit(); db.close()
    monkeypatch.setattr(watchdog, "OPENCLAW_DB", db_path)
    assert watchdog.check_cron_errors() is None


def test_watchdog_alarm_dedup(monkeypatch):
    recent = datetime.now(UTC).isoformat(timespec="seconds")
    stale = (datetime.now(UTC) - timedelta(hours=watchdog.REALARM_HOURS + 1)).isoformat(
        timespec="seconds")
    assert watchdog._should_alarm("stale_mail", {}) is True
    assert watchdog._should_alarm("stale_mail", {"stale_mail": recent}) is False
    assert watchdog._should_alarm("stale_mail", {"stale_mail": stale}) is True
