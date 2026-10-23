"""Full mailbox management for the operator assistant (Halim).

ops_inbox_triage.py only ever READS (BODY.PEEK, never touches flags). This
script is the write side: once Halim has handled a message he can mark it
read, archive it or label it — so arifi.arber@gmail.com is actually MANAGED,
not just watched. Uses the same IMAP credentials as triage (backend/.env),
no Gmail API / OAuth / PubSub (the existing IMAP path is enough and the
D-063 watchdog already covers failure).

CRITICAL SAFETY — the matter-alias firewall: every matter has a plus-address
`<user>+<token>@<domain>` (email_ingest.py). Incoming mail to those aliases
must stay UNSEEN until email_ingest's UNSEEN poller files it into the matter.
So mark-read / archive REFUSE to touch any message addressed to a `+token@`
alias — Halim can never accidentally swallow a client's mail before it
becomes a matter note.

Commands (all print JSON):
    unread-count
    search "<imap-query>" [--limit N]     # e.g. 'FROM bank UNSEEN'
    read <uid>                            # headers + body snippet (read-only)
    mark-read <uid> [<uid> ...]
    archive <uid> [<uid> ...]             # remove \\Inbox (Gmail: move out of Inbox)
    label <uid> "<Gmail label>"           # add an X-GM-LABELS label
"""
import argparse
import email
import email.header
import email.utils
import imaplib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402

MAX_SNIPPET = 2000
# Same pattern email_ingest uses to recognize a matter alias — keep in sync.
_TOKEN_RE = re.compile(r"\+([a-z0-9]{10,32})@", re.IGNORECASE)


def _credentials() -> tuple[str, int, str, str]:
    if settings.imap_host:
        return (settings.imap_host, settings.imap_port,
                settings.imap_user, settings.imap_password)
    host = "imap.gmail.com" if "gmail" in settings.smtp_host else settings.smtp_host
    return host, 993, settings.smtp_user, settings.smtp_password


def _decode(value: str | None) -> str:
    if not value:
        return ""
    out = []
    for text, charset in email.header.decode_header(value):
        if isinstance(text, bytes):
            try:
                out.append(text.decode(charset or "utf-8", errors="replace"))
            except LookupError:
                out.append(text.decode("utf-8", errors="replace"))
        else:
            out.append(text)
    return " ".join(out).strip()


def _recipients(msg: email.message.Message) -> str:
    return " ".join(_decode(msg.get(h)) for h in ("To", "Cc", "Delivered-To"))


def _is_matter_alias(msg: email.message.Message) -> bool:
    """True when the mail is addressed to a matter's +token@ alias — off limits
    for flag changes until email_ingest has filed it."""
    return bool(_TOKEN_RE.search(_recipients(msg)))


def _body_snippet(msg: email.message.Message) -> str:
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
    try:
        text = raw.decode(charset, errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    return text.strip()[:MAX_SNIPPET]


def _connect(readonly: bool) -> imaplib.IMAP4_SSL:
    host, port, user, password = _credentials()
    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(user, password)
    imap.select("INBOX", readonly=readonly)
    return imap


def _fetch(imap: imaplib.IMAP4_SSL, uid: int) -> email.message.Message | None:
    status, data = imap.uid("FETCH", str(uid), "(BODY.PEEK[])")
    if status != "OK" or not data or data[0] is None:
        return None
    return email.message_from_bytes(data[0][1])


def _guard_aliases(imap: imaplib.IMAP4_SSL, uids: list[int]) -> list[int]:
    """Drop any UID that belongs to a matter alias; return the safe ones."""
    safe = []
    for uid in uids:
        msg = _fetch(imap, uid)
        if msg is not None and _is_matter_alias(msg):
            continue
        safe.append(uid)
    return safe


def cmd_unread_count() -> dict:
    imap = _connect(readonly=True)
    try:
        status, data = imap.uid("SEARCH", None, "UNSEEN")
        uids = data[0].split() if status == "OK" and data and data[0] else []
        oldest = None
        if uids:
            msg = _fetch(imap, int(uids[0].split()[0] if isinstance(uids[0], bytes) else uids[0]))
            if msg:
                oldest = {"from": _decode(msg.get("From")),
                          "subject": _decode(msg.get("Subject")),
                          "date": _decode(msg.get("Date"))}
        return {"unread": len(uids), "oldest_unread": oldest}
    finally:
        imap.logout()


def cmd_search(query: str, limit: int) -> dict:
    imap = _connect(readonly=True)
    try:
        status, data = imap.uid("SEARCH", None, query)
        if status != "OK":
            return {"error": f"search failed: {data}"}
        uids = [int(u) for u in (data[0].split() if data and data[0] else [])]
        results = []
        for uid in sorted(uids, reverse=True)[:limit]:
            msg = _fetch(imap, uid)
            if not msg:
                continue
            results.append({
                "uid": uid,
                "from": _decode(msg.get("From")),
                "subject": _decode(msg.get("Subject")),
                "date": _decode(msg.get("Date")),
                "matter_alias": _is_matter_alias(msg),
            })
        return {"count": len(uids), "shown": len(results), "messages": results}
    finally:
        imap.logout()


def cmd_read(uid: int) -> dict:
    imap = _connect(readonly=True)  # PEEK — reading never changes the flag
    try:
        msg = _fetch(imap, uid)
        if not msg:
            return {"error": f"uid {uid} not found"}
        return {
            "uid": uid,
            "from": _decode(msg.get("From")),
            "to": _decode(msg.get("To")),
            "cc": _decode(msg.get("Cc")),
            "subject": _decode(msg.get("Subject")),
            "date": _decode(msg.get("Date")),
            "message_id": str(msg.get("Message-ID") or "").strip(),
            "matter_alias": _is_matter_alias(msg),
            "body": _body_snippet(msg),
        }
    finally:
        imap.logout()


def cmd_mark_read(uids: list[int]) -> dict:
    imap = _connect(readonly=False)
    try:
        safe = _guard_aliases(imap, uids)
        skipped = sorted(set(uids) - set(safe))
        done = []
        for uid in safe:
            status, _ = imap.uid("STORE", str(uid), "+FLAGS", "(\\Seen)")
            if status == "OK":
                done.append(uid)
        return {"marked_read": done, "skipped_matter_alias": skipped}
    finally:
        imap.logout()


def cmd_archive(uids: list[int]) -> dict:
    """Remove from Inbox. On Gmail, deleting the special \\Inbox label via
    X-GM-LABELS archives the thread (it is not trashed)."""
    imap = _connect(readonly=False)
    try:
        safe = _guard_aliases(imap, uids)
        skipped = sorted(set(uids) - set(safe))
        done = []
        for uid in safe:
            status, _ = imap.uid("STORE", str(uid), "-X-GM-LABELS", "(\\Inbox)")
            if status == "OK":
                imap.uid("STORE", str(uid), "+FLAGS", "(\\Seen)")
                done.append(uid)
        return {"archived": done, "skipped_matter_alias": skipped}
    finally:
        imap.logout()


def cmd_label(uid: int, label: str) -> dict:
    imap = _connect(readonly=False)
    try:
        if _is_matter_alias(_fetch(imap, uid) or email.message.Message()):
            return {"error": "refused: message belongs to a matter alias", "uid": uid}
        # Gmail label values with spaces must be quoted inside the parens.
        value = f'("{label}")' if " " in label else f"({label})"
        status, data = imap.uid("STORE", str(uid), "+X-GM-LABELS", value)
        return {"labeled": uid, "label": label, "ok": status == "OK"}
    finally:
        imap.logout()


def main() -> dict:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("unread-count")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    r = sub.add_parser("read")
    r.add_argument("uid", type=int)
    mr = sub.add_parser("mark-read")
    mr.add_argument("uid", type=int, nargs="+")
    ar = sub.add_parser("archive")
    ar.add_argument("uid", type=int, nargs="+")
    lb = sub.add_parser("label")
    lb.add_argument("uid", type=int)
    lb.add_argument("label")
    args = ap.parse_args()

    host, _, user, password = _credentials()
    if not user or not password:
        return {"error": "IMAP/SMTP credentials not configured in backend/.env"}

    if args.cmd == "unread-count":
        return cmd_unread_count()
    if args.cmd == "search":
        return cmd_search(args.query, args.limit)
    if args.cmd == "read":
        return cmd_read(args.uid)
    if args.cmd == "mark-read":
        return cmd_mark_read(args.uid)
    if args.cmd == "archive":
        return cmd_archive(args.uid)
    if args.cmd == "label":
        return cmd_label(args.uid, args.label)
    return {"error": f"unknown command {args.cmd}"}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2, default=str))
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
