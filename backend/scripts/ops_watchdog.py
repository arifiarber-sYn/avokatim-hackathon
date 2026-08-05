"""Independent mail-pipeline watchdog — NO LLM anywhere in the chain.

Born from the Vuksani incident (2026-08-04): a lawyer's reply sat unanswered
for 4.7 hours because the LLM behind Halim's triage cron timed out repeatedly,
and nothing else was watching. The protocol rule "notify after 2 consecutive
errors" cannot save us when the notifier itself is the thing that is down.

This script is pure Python + IMAP + Telegram Bot API and runs from its own
systemd timer (every 30 min). It alarms the owner directly when:

1. STALE MAIL — the inbox holds messages newer than the triage state
   (data/ops/inbox_state.json) that are older than STALE_AFTER_MIN minutes,
   i.e. mail arrived and nobody processed it.
2. CRON ERRORS — the OpenClaw run log (state/openclaw.sqlite, read-only)
   shows ERROR_STREAK consecutive failed runs of the triage job with no
   success after them.

Alarms deduplicate via data/ops/watchdog_state.json (one alarm per condition
per REALARM_HOURS). Telegram credentials come from ~/.openclaw/openclaw.json
(bot token) + the allowFrom chat id — no new secrets. If Telegram fails, we
fall back to an email to the operator (different failure domain: SMTP send
still works when the LLM is down).

Usage:
    python scripts/ops_watchdog.py            # check + alarm if needed
    python scripts/ops_watchdog.py --status   # print findings, never alarm
"""
import email.utils
import imaplib
import json
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import PROJECT_DIR, settings  # noqa: E402

INBOX_STATE = PROJECT_DIR / "data" / "ops" / "inbox_state.json"
WATCHDOG_STATE = PROJECT_DIR / "data" / "ops" / "watchdog_state.json"
HEARTBEAT = PROJECT_DIR / "data" / "ops" / "halim_heartbeat.txt"
OPENCLAW_CFG = Path.home() / ".openclaw" / "openclaw.json"
OPENCLAW_DB = Path.home() / ".openclaw" / "state" / "openclaw.sqlite"
TRIAGE_JOB_NAME = "avokatim-inbox-triage"

STALE_AFTER_MIN = 60      # unprocessed mail older than this -> alarm
ERROR_STREAK = 3          # consecutive failed cron runs -> alarm
HEARTBEAT_STALE_MIN = 70  # no OpenClaw heartbeat for this long -> scheduler dead
REALARM_HOURS = 3         # don't repeat the same alarm more often than this
STATUS_ONLY = "--status" in sys.argv


# --- alerting (LLM-free) -----------------------------------------------------

def _telegram_creds() -> tuple[str, str] | None:
    try:
        tg = json.loads(OPENCLAW_CFG.read_text())["channels"]["telegram"]
        token = tg.get("botToken") or ""
        chat = str(settings.openclaw_hook_to or (tg.get("allowFrom") or [""])[0])
        if token and chat:
            return token, chat
    except Exception:
        pass
    return None


def send_alarm(text: str) -> str:
    """Telegram first (direct Bot API), operator email as fallback.
    Returns the channel that worked ('' when everything failed)."""
    creds = _telegram_creds()
    if creds:
        token, chat = creds
        try:
            data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage", data=data)
            with urllib.request.urlopen(req, timeout=15) as resp:
                if json.loads(resp.read()).get("ok"):
                    return "telegram"
        except Exception:
            pass
    try:
        import smtplib
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = settings.smtp_user
        msg["Subject"] = "[WATCHDOG] AvokatIM — posta ka ngecur"
        msg.set_content(text)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as s:
            if settings.smtp_starttls:
                s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return "email"
    except Exception:
        return ""


# --- checks -------------------------------------------------------------------

def check_stale_mail() -> str | None:
    """Mail newer than the triage state and older than STALE_AFTER_MIN min."""
    try:
        last_uid = int(json.loads(INBOX_STATE.read_text()).get("last_uid", 0))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return "inbox_state.json mungon/i palexueshëm — triage s'ka punuar kurrë?"
    if not last_uid:
        return None

    host = settings.imap_host or (
        "imap.gmail.com" if "gmail" in settings.smtp_host else settings.smtp_host)
    user = settings.imap_user or settings.smtp_user
    password = settings.imap_password or settings.smtp_password
    imap = imaplib.IMAP4_SSL(host, settings.imap_port if settings.imap_host else 993)
    try:
        imap.login(user, password)
        imap.select("INBOX", readonly=True)
        status, data = imap.uid("SEARCH", None, f"UID {last_uid + 1}:*")
        uids = [int(u) for u in (data[0].split() if status == "OK" and data and data[0] else [])]
        uids = [u for u in uids if u > last_uid]
        if not uids:
            return None
        # Age of the OLDEST unprocessed message decides.
        oldest = min(uids)
        status, md = imap.uid("FETCH", str(oldest),
                              "(BODY.PEEK[HEADER.FIELDS (DATE)])")
        if status != "OK" or not md or md[0] is None:
            return None
        raw = md[0][1].decode(errors="replace")
        date_hdr = raw.split(":", 1)[1].strip() if ":" in raw else ""
        try:
            arrived = email.utils.parsedate_to_datetime(date_hdr)
        except (TypeError, ValueError):
            return None
        age_min = (datetime.now(UTC) - arrived).total_seconds() / 60
        if age_min >= STALE_AFTER_MIN:
            return (f"{len(uids)} email të papërpunuar në inbox; më i vjetri "
                    f"pret prej {age_min:.0f} min (UID {oldest}). Triage-i i "
                    f"Halimit s'po i merr.")
        return None
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def check_cron_errors() -> str | None:
    """ERROR_STREAK consecutive failures of the triage cron, none resolved."""
    if not OPENCLAW_DB.exists():
        return None
    db = sqlite3.connect(f"file:{OPENCLAW_DB}?mode=ro", uri=True)
    try:
        job = db.execute(
            "SELECT job_id FROM cron_jobs WHERE name = ?", (TRIAGE_JOB_NAME,)
        ).fetchone()
        if not job:
            return f"cron job '{TRIAGE_JOB_NAME}' nuk ekziston më në OpenClaw!"
        rows = db.execute(
            "SELECT status, error, run_at_ms FROM cron_run_logs "
            "WHERE job_id = ? ORDER BY run_at_ms DESC LIMIT ?",
            (job[0], ERROR_STREAK),
        ).fetchall()
    finally:
        db.close()
    if len(rows) < ERROR_STREAK:
        return None
    if all(r[0] == "error" for r in rows):
        newest = datetime.fromtimestamp(rows[0][2] / 1000, tz=UTC)
        reason = (rows[0][1] or "")[:120]
        return (f"{ERROR_STREAK} dështime radhazi të cron-it të triage "
                f"(i fundit {newest:%H:%M} UTC): {reason}")
    return None


# --- dedup + main --------------------------------------------------------------

def _should_alarm(key: str, state: dict) -> bool:
    last = state.get(key)
    if not last:
        return True
    try:
        return datetime.now(UTC) - datetime.fromisoformat(last) > timedelta(
            hours=REALARM_HOURS)
    except ValueError:
        return True


def check_heartbeat() -> str | None:
    """OpenClaw's own cron writes HEARTBEAT every 30 min (D-065). If it goes
    stale, the scheduler itself is down — nothing inside OpenClaw could tell us,
    so this external timer must. Absent file on a fresh install is not an alarm.
    """
    if not HEARTBEAT.exists():
        return None
    age_min = (datetime.now(UTC).timestamp() - HEARTBEAT.stat().st_mtime) / 60
    if age_min > HEARTBEAT_STALE_MIN:
        return (f"OpenClaw-i s'ka shkruar heartbeat prej {age_min:.0f} min "
                f"(pragu {HEARTBEAT_STALE_MIN}). Skeduluesi/gateway-i i Halimit "
                f"mund të jetë i vdekur — kontrollo openclaw-gateway.service.")
    return None


def main() -> int:
    findings: list[tuple[str, str]] = []
    for key, check in (("stale_mail", check_stale_mail),
                       ("cron_errors", check_cron_errors),
                       ("heartbeat", check_heartbeat)):
        try:
            problem = check()
        except Exception as exc:
            problem = f"watchdog vetë dështoi në kontrollin '{key}': {exc}"
        if problem:
            findings.append((key, problem))

    if STATUS_ONLY:
        print(json.dumps({"findings": dict(findings) or "OK",
                          "checked_at": datetime.now(UTC).isoformat(timespec="seconds")},
                         ensure_ascii=False, indent=2))
        return 0

    if not findings:
        print("OK — posta po përpunohet, cron-i i triage në rregull")
        return 0

    try:
        state = json.loads(WATCHDOG_STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}

    for key, problem in findings:
        if not _should_alarm(key, state):
            print(f"({key}: alarmuar tashmë brenda {REALARM_HOURS}h — heshtje)")
            continue
        text = ("⚠️ WATCHDOG AvokatIM (pa LLM):\n" + problem +
                "\n\nKontrollo Halimin/triage-in. Ky alarm vjen direkt nga "
                "systemd, jo nga Halimi.")
        channel = send_alarm(text)
        print(f"ALARM ({key}) → {channel or 'DËSHTOI çdo kanal!'}: {problem}")
        if channel:
            state[key] = datetime.now(UTC).isoformat(timespec="seconds")

    WATCHDOG_STATE.parent.mkdir(parents=True, exist_ok=True)
    WATCHDOG_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return 1


if __name__ == "__main__":
    sys.exit(main())
