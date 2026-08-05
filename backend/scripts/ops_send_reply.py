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
import json
import mimetypes
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.services.notifications import _is_test_recipient  # noqa: E402


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
    return {"sent": True, "to": args.to, "subject": args.subject,
            "attachments": len(args.attach)}


if __name__ == "__main__":
    try:
        result = main()
    except Exception as exc:
        result = {"sent": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("sent") else 1)
