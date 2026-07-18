"""Read-only triage of the operator's Gmail inbox for the OpenClaw assistant.

Runs from an OpenClaw cron job every ~10 minutes. Fetches messages newer than
the last seen UID with BODY.PEEK (never marks anything read, never deletes),
classifies them and prints a JSON report to stdout:

- "human":  real correspondence (lawyers/notaries/citizens) that may need a
            reply — full sender/subject/snippet so the assistant can draft one.
- "system": notifications sent by AvokatIM itself (From = our own address) —
            counted only; real-time platform events arrive via ops_notify.
- "bounce": mailer-daemon bounces — counted only, surfaced when spiking.

State (last UID per mailbox) lives in data/ops/inbox_state.json so restarts
and reboots never re-report old mail. Exit code is always 0 with valid JSON;
errors are reported inside the JSON ("error" key) to keep the cron quiet.
"""
import email
import email.header
import email.utils
import imaplib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import PROJECT_DIR, settings  # noqa: E402

STATE_FILE = PROJECT_DIR / "data" / "ops" / "inbox_state.json"
MAX_SNIPPET = 1200
MAX_HUMAN_PER_RUN = 10

BOUNCE_FROM_RE = re.compile(
    r"(mailer-daemon|postmaster|mail delivery (subsystem|system)|delivery status)",
    re.IGNORECASE,
)
# Our own outbound identity: notifications AvokatIM sends to the operator
_SELF_ADDRESSES = {
    settings.smtp_user.lower(),
    email.utils.parseaddr(settings.smtp_from)[1].lower(),
}


def _imap_credentials() -> tuple[str, int, str, str]:
    """Prefer explicit IMAP settings; fall back to the Gmail SMTP account
    (the same app password works for IMAP)."""
    if settings.imap_host:
        return settings.imap_host, settings.imap_port, settings.imap_user, settings.imap_password
    host = "imap.gmail.com" if "gmail" in settings.smtp_host else settings.smtp_host
    return host, 993, settings.smtp_user, settings.smtp_password


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = email.header.decode_header(value)
    out = []
    for text, charset in parts:
        if isinstance(text, bytes):
            out.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            out.append(text)
    return " ".join(out).strip()


def _body_snippet(msg: email.message.Message) -> str:
    """First text/plain part, decoded, trimmed of quoted history."""
    payload = None
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                payload = part
                break
    else:
        payload = msg
    if payload is None:
        return ""
    raw = payload.get_payload(decode=True) or b""
    charset = payload.get_content_charset() or "utf-8"
    text = raw.decode(charset, errors="replace")
    # Cut quoted reply history ("On ... wrote:" / "> ...")
    lines = []
    for line in text.splitlines():
        if line.startswith(">") or re.match(r"^On .{5,80} wrote:$", line.strip()):
            break
        lines.append(line)
    return "\n".join(lines).strip()[:MAX_SNIPPET]


def _classify(from_addr: str, subject: str) -> str:
    if BOUNCE_FROM_RE.search(from_addr) or BOUNCE_FROM_RE.search(subject):
        return "bounce"
    addr = email.utils.parseaddr(from_addr)[1].lower()
    if addr in _SELF_ADDRESSES:
        return "system"
    return "human"


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def run() -> dict:
    host, port, user, password = _imap_credentials()
    if not user or not password:
        return {"error": "IMAP/SMTP credentials not configured in backend/.env"}

    state = _load_state()
    report: dict = {
        "checked_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "mailbox": user,
        "human": [],
        "system_count": 0,
        "bounce_count": 0,
    }

    imap = imaplib.IMAP4_SSL(host, port)
    try:
        imap.login(user, password)
        status, data = imap.select("INBOX", readonly=True)
        if status != "OK":
            return {"error": f"cannot select INBOX: {data}"}

        last_uid = int(state.get("last_uid", 0))
        if last_uid:
            status, data = imap.uid("SEARCH", None, f"UID {last_uid + 1}:*")
        else:
            # First run: baseline only — remember the newest UID, report nothing
            # (otherwise the whole historic inbox would flood the assistant).
            status, data = imap.uid("SEARCH", None, "ALL")
            uids = [int(u) for u in (data[0].split() if data and data[0] else [])]
            state["last_uid"] = max(uids) if uids else 0
            _save_state(state)
            report["baseline"] = True
            report["baseline_uid"] = state["last_uid"]
            return report

        uids = [int(u) for u in (data[0].split() if status == "OK" and data and data[0] else [])]
        # Gmail returns the last message for "N+1:*" when nothing is newer
        uids = [u for u in uids if u > last_uid]
        if not uids:
            return report

        for uid in sorted(uids):
            status, msg_data = imap.uid("FETCH", str(uid), "(BODY.PEEK[])")
            if status != "OK" or not msg_data or msg_data[0] is None:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            from_h = _decode(msg.get("From"))
            subject = _decode(msg.get("Subject"))
            kind = _classify(from_h, subject)
            if kind == "bounce":
                report["bounce_count"] += 1
            elif kind == "system":
                report["system_count"] += 1
            elif len(report["human"]) < MAX_HUMAN_PER_RUN:
                report["human"].append({
                    "uid": uid,
                    "from": from_h,
                    "reply_to": email.utils.parseaddr(
                        _decode(msg.get("Reply-To") or msg.get("From"))
                    )[1],
                    "subject": subject,
                    "date": _decode(msg.get("Date")),
                    "message_id": (msg.get("Message-ID") or "").strip(),
                    "snippet": _body_snippet(msg),
                })

        state["last_uid"] = max(uids)
        state["last_run"] = report["checked_at"]
        _save_state(state)
        return report
    finally:
        try:
            imap.logout()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        result = run()
    except Exception as exc:  # keep the cron output machine-readable
        result = {"error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
