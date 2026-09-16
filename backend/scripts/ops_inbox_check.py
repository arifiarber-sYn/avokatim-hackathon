#!/usr/bin/env python3
"""ops_inbox_check.py — read-only inbox triage for the assistant cron.

What it does:
  - Connects to Gmail (App Password) via IMAP, readonly.
  - Keeps a persistent `last_uid` cursor so each run only sees NEW mail.
  - On the first run it records the newest UID as a baseline and reports
    nothing else (so the whole historic inbox never floods the assistant).
  - Classifies new mail into: human (Korsia AvokatIM — needs a reply),
    company (Track A M&A — needs a reply), system/bounce/optout (noise).
  - Prints one JSON report on stdout — machine-readable, ready for the
    OpenClaw assistant to act on.

It does NOT send anything, change flags, or move folders. It is a pure
sensor. The assistant reads the report, drafts, sends (via the existing
ops_send_reply tooling), then calls `ops_inbox_ack.py` to advance the
cursor. If the assistant does nothing, the cursor stays where it is —
nothing is ever lost.

Env:
  GMAIL_USER, GMAIL_PASS  (App Password)
  AVO_HOST, AVO_PORT      (defaults: gmail.com / 993)
  AVO_STATE_DIR           (default: ~/.openclaw/state)
"""

from __future__ import annotations

import email
import email.utils
import imaplib
import json
import os
import re
import sys
from datetime import datetime, UTC

# ── config ──────────────────────────────────────────────────────────────────
HOST = os.environ.get("AVO_HOST", "gmail.com")
PORT = int(os.environ.get("AVO_PORT", "993"))
STATE_DIR = os.path.expanduser(os.environ.get("AVO_STATE_DIR", "~/.openclaw/state"))
STATE_PATH = os.path.join(STATE_DIR, "inbox_check_state.json")
COMPANY_DOMAINS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "company_domains.json"
)

# Classification
HUMAN_DOMAINS = {"avokatim.com", "avokati.org", "arber.kajafaj.net"}
BOUNCE_RE = re.compile(
    r"(mailer-daemon|postmaster|delivery failure|could not be delivered|"
    r"undelivered|mailbox unavailable|user unknown|no such user)",
    re.I,
)
SYSTEM_RE = re.compile(
    r"(notification|update|alert|reminder|invoice|receipt|billing|"
    r"newsletter|digest|no-reply|noreply|donotreply|do-not-reply|security|"
    r"password|subscription|github|gitlab|slack|discord|figma|zoom|calendly|"
    r"linkedin|stripe|paypal|bank|visa|mastercard|amex|klarna|revolut|"
    r"transferwise|wise|binance|coinbase|twitch|tumblr|instagram|tiktok|"
    r"youtube|google|apple|icloud|outlook|yahoo|proton|hey\.com|fastmail)",
    re.I,
)
OPTOUT_RE = re.compile(
    r"(unsubscribe|opt.?out|remove me|stop emailing|take me off|"
    r"unsubscribe from this|click here to unsubscribe|cancel this)",
    re.I,
)
OPTOUT_STATE = os.path.join(STATE_DIR, "inbox_optouts.json")

# Cap per run: at most N human mail per run so a backlog after an outage
# doesn't flood the assistant; the cursor stops before the rest so it is
# never lost.
MAX_HUMAN_PER_RUN = int(os.environ.get("AVO_MAX_HUMAN_PER_RUN", "10"))

# ── state ───────────────────────────────────────────────────────────────────


def _load_state() -> dict:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def _record_company_reply(domain: str) -> None:
    """Remember which company domains recently replied (Track A signal)."""
    if not domain:
        return
    path = os.path.join(STATE_DIR, "company_replies.json")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data[domain] = now
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _record_optout(addr: str) -> bool:
    """Remember an opted-out sender so future cold mail from them is silenced.

    Returns True if this was a NEW optout (not seen before).
    """
    try:
        with open(OPTOUT_STATE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    if addr.lower() in data:
        return False
    data[addr.lower()] = datetime.now(UTC).isoformat(timespec="seconds")
    try:
        with open(OPTOUT_STATE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
    return True


def _company_domains() -> list[tuple[str, str]]:
    try:
        with open(COMPANY_DOMAINS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    out = []
    for c in data.get("companies", []):
        for d in c.get("domains", []):
            out.append((d.lower(), c.get("name", "")))
    return out


def _match_company(addr: str, domains: list[tuple[str, str]]) -> tuple[str, str] | None:
    for d, name in domains:
        if addr.endswith(d):
            return d, name
    return None


def _decode(value):
    if not value:
        return ""
    try:
        if isinstance(value, tuple) and value[1] is None:
            return value[0]
        return value
    except Exception:
        return str(value)


def _body_snippet(msg: "email.message.Message") -> str:
    payload = msg.get_payload(decode=True)
    if payload is None and msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                break
    if payload is None:
        return ""
    charset = payload.headers.get("Content-Type", [None, {}])[1].get("charset") if hasattr(payload, "headers") else None
    try:
        text = payload.decode(charset or "utf-8", errors="replace")
    except Exception:
        text = payload.decode("utf-8", errors="replace")
    return " ".join(text.split())[:300]


def _classify(from_h: str, subject: str, snippet: str, company_domains) -> str:
    """Return one of: human | company | bounce | optout | system | unknown."""
    sender = email.utils.parseaddr(from_h)[1].lower()
    subj = (subject or "").lower()
    body = (snippet or "").lower()

    if BOUNCE_RE.search(subj) or BOUNCE_RE.search(body[:400]) or "mailer-daemon" in sender:
        return "bounce"
    if OPTOUT_RE.search(subj) or OPTOUT_RE.search(body[:600]):
        return "optout"
    if sender in HUMAN_DOMAINS or any(sender.endswith(d) for d in HUMAN_DOMAINS):
        return "human"
    if _match_company(sender, company_domains):
        return "company"
    if SYSTEM_RE.search(subj) or SYSTEM_RE.search(sender):
        return "system"
    return "unknown"


# ── main ────────────────────────────────────────────────────────────────────


def run() -> dict:
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_PASS")
    if not user or not password:
        return {"error": "GMAIL_USER / GMAIL_PASS env not set"}

    state = _load_state()
    report: dict = {
        "checked_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "mailbox": user,
        # Track A M&A replies first — highest-value mail in the box.
        "company": [],
        "human": [],
        "system_count": 0,
        "bounce_count": 0,
        "optout_count": 0,
        "optouts": [],
    }
    company_domains = _company_domains()

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

        # last_uid must never advance past an UNREPORTED human mail: after a
        # long outage the backlog can exceed MAX_HUMAN_PER_RUN, and the old
        # behavior (always advancing to max(uids)) silently lost the rest
        # forever. Now we stop at the cap and the next run picks up there.
        processed_up_to = last_uid
        for uid in sorted(uids):
            status, msg_data = imap.uid("FETCH", str(uid), "(BODY.PEEK[])")
            if status != "OK" or not msg_data or msg_data[0] is None:
                processed_up_to = uid  # unfetchable — skip, don't loop on it
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            from_h = _decode(msg.get("From"))
            subject = _decode(msg.get("Subject"))
            snippet = _body_snippet(msg)
            kind = _classify(from_h, subject, snippet, company_domains)
            if kind == "human" and len(report["human"]) >= MAX_HUMAN_PER_RUN:
                report["truncated"] = True
                report["truncated_at_uid"] = uid
                break
            if kind == "bounce":
                report["bounce_count"] += 1
            elif kind == "system":
                report["system_count"] += 1
            elif kind == "company":
                reply_to = email.utils.parseaddr(
                    _decode(msg.get("Reply-To") or msg.get("From"))
                )[1]
                sender = email.utils.parseaddr(from_h)[1].lower()
                target_domain, name = _match_company(sender, company_domains) or ("", "")
                _record_company_reply(target_domain)
                report["company"].append({
                    "uid": uid,
                    "lead": f"LEAD M&A — përgjigje nga {name}",
                    "company": name,
                    "from": from_h,
                    "reply_to": reply_to,
                    "subject": subject,
                    "date": _decode(msg.get("Date")),
                    "message_id": str(msg.get("Message-ID") or "").strip(),
                    "snippet": snippet,
                })
            elif kind == "optout":
                # Silence future cold mail; do NOT hand it to Halim to answer.
                addr = email.utils.parseaddr(
                    _decode(msg.get("Reply-To") or msg.get("From"))
                )[1]
                report["optout_count"] += 1
                if _record_optout(addr):
                    report["optouts"].append(addr)
            else:
                report["human"].append({
                    "uid": uid,
                    "from": from_h,
                    "reply_to": email.utils.parseaddr(
                        _decode(msg.get("Reply-To") or msg.get("From"))
                    )[1],
                    "subject": subject,
                    "date": _decode(msg.get("Date")),
                    "message_id": str(msg.get("Message-ID") or "").strip(),
                    "snippet": snippet,
                })
            processed_up_to = uid

        state["last_uid"] = processed_up_to
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
