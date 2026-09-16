"""Send an operator email reply — used by the OpenClaw assistant ONLY after
the owner explicitly approves the draft on Telegram (guardrail: the assistant
never sends mail on its own initiative).

Usage:
    ops_send_reply.py --to someone@example.com --subject "Re: ..." \
        [--in-reply-to "<message-id>"] [--attach path.pdf ...] < body.txt

The body is read from stdin (UTF-8) so drafts with any quoting/newlines pass
safely. --attach may be repeated (e.g. to attach the platform offer PDF for a
company outreach). Refuses test/simulation recipients. Prints a JSON result.
"""
import argparse
import csv
import hashlib
import json
import mimetypes
import smtplib
import sys
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import PROJECT_DIR, settings  # noqa: E402
from app.services.notifications import _is_test_recipient  # noqa: E402

# Correspondence ledger: every operator send lands here so the owner has a
# full audit trail of what Halim sent in his name (surfaced by ops_digest).
REPLIES_LOG = PROJECT_DIR / "data" / "ops" / "replies_log.csv"


def _log_send(to: str, subject: str, body: str, attachments: int) -> None:
    REPLIES_LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not REPLIES_LOG.exists()
    with REPLIES_LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["sent_at", "to", "subject", "attachments", "body_sha256"])
        w.writerow([
            datetime.now(UTC).isoformat(timespec="seconds"), to, subject,
            attachments, hashlib.sha256(body.encode()).hexdigest()[:16],
        ])


def main() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--in-reply-to", default="")
    parser.add_argument("--attach", action="append", default=[],
                        help="file to attach (repeatable)")
    args = parser.parse_args()

    body = sys.stdin.read().strip()
    if not body:
        return {"sent": False, "error": "empty body on stdin"}
    if not settings.smtp_host:
        return {"sent": False, "error": "SMTP not configured"}
    if _is_test_recipient(args.to):
        return {"sent": False, "error": f"refusing test/simulation recipient {args.to}"}

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = args.to
    msg["Subject"] = args.subject
    if args.in_reply_to:
        msg["In-Reply-To"] = args.in_reply_to
        msg["References"] = args.in_reply_to
    msg.set_content(body)

    for path_str in args.attach:
        p = Path(path_str)
        if not p.is_file():
            return {"sent": False, "error": f"attachment not found: {path_str}"}
        ctype, _ = mimetypes.guess_type(p.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=maintype,
                           subtype=subtype, filename=p.name)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        if settings.smtp_starttls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    _log_send(args.to, args.subject, body, len(args.attach))
    return {"sent": True, "to": args.to, "subject": args.subject,
            "attachments": len(args.attach)}


# --- Ops send-reply guard hook (Halim D-139, 2026-08-18) ---
# Before sending, run the shared guard check. If it returns allow:false,
# abort with a clear message and do NOT send.
# Entity: sekretari | Domain: email_avokatim (korsia AvokatIM) / email_personal
def _guard_check(action: str, domain: str = "email_avokatim") -> None:
    import os
    import subprocess
    guard = os.path.expanduser("~/scripts/halim_guard.py")
    if not os.path.exists(guard):
        return  # guard not installed; proceed
    r = subprocess.run(
        [sys.executable, guard, "check",
         "--entity", "sekretari",
         "--domain", domain,
         "--action", action],
        capture_output=True, text=True, timeout=10
    )
    if r.returncode != 0:
        sys.exit(f"GUARD BLOCKED: {r.stderr.strip() or r.stdout.strip()}")


if __name__ == "__main__":
    _guard_check("send_reply")  # SystemExit before any SMTP work if blocked
    try:
        result = main()
    except Exception as exc:
        result = {"sent": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("sent") else 1)
