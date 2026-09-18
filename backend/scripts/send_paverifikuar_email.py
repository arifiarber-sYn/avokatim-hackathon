"""Send the AvokatIM "profile is one step from visibility" email (segment #1).

Owner-commissioned campaign (Kllosha, 2026-09-18 15:50): the action email for
the VISIBLE but NOT-VERIFIED lawyers (lawyer_profiles.is_visible = true AND
verification_status <> 'verified'), so they complete the profile and get
verified.

Same sending identity/path as the day's demo campaign (Gmail SMTP via
settings.*). Plain-text alternative + small HTML body, one personalised
greeting per recipient.

Safety:
- halim_guard check before any SMTP work (abort if blocked);
- refuses test/simulation recipients (_is_test_recipient);
- dedup against this campaign's ledger: an address already logged `ok` for
  this --tag is never sent twice;
- writes a ledger row per recipient (data/ops/paverifikuar_sent.csv).

Usage:
    python scripts/send_paverifikuar_email.py --recipients r.csv \
        --subject "..." --html body.html --text body.txt [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import smtplib
import sys
import time
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import PROJECT_DIR, settings  # noqa: E402
from app.services.notifications import _is_test_recipient  # noqa: E402

LOG = PROJECT_DIR / "data" / "ops" / "paverifikuar_sent.csv"
TAG = "paverifikuar-2026-09-18"


def _guard_check(action: str) -> None:
    import os
    import subprocess
    guard = os.path.expanduser("~/scripts/halim_guard.py")
    if not os.path.exists(guard):
        return
    r = subprocess.run(
        [sys.executable, guard, "check", "--entity", "sekretari",
         "--domain", "email_avokatim", "--action", action],
        capture_output=True, text=True, timeout=15,
    )
    if r.returncode != 0:
        sys.exit(f"GUARD BLOCKED: {r.stderr.strip() or r.stdout.strip()}")


def _already_sent(tag: str) -> set[str]:
    done: set[str] = set()
    if LOG.exists():
        with LOG.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("tag") == tag and row.get("status") == "ok":
                    done.add(row.get("email", "").lower())
    return done


def _log(rows: list[dict]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["sent_at", "tag", "email", "name", "status", "detail"]
        )
        if new:
            w.writeheader()
        w.writerows(rows)


def build(recipient_email: str, name: str, subject: str, html: str,
          text: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(text.replace("{{EMRI}}", name))
    msg.add_alternative(html.replace("{{EMRI}}", name), subtype="html")
    return msg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipients", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--html", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    html = Path(args.html).read_text(encoding="utf-8")
    text = Path(args.text).read_text(encoding="utf-8")

    recips = list(csv.DictReader(Path(args.recipients).open(encoding="utf-8")))
    if args.limit:
        recips = recips[: args.limit]
    done = _already_sent(TAG)

    todo, skipped = [], []
    for r in recips:
        email = r["email"].strip()
        if email.lower() in done:
            skipped.append((email, "already-sent"))
        elif _is_test_recipient(email):
            skipped.append((email, "test-recipient"))
        else:
            todo.append(r)

    plan = {"recipients": len(recips), "to_send": len(todo),
            "skipped": skipped, "dry_run": args.dry_run,
            "subject": args.subject,
            "targets": [r["email"] for r in todo]}
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    if not todo:
        print(json.dumps({"ok": True, "sent": 0, "skipped": skipped},
                         ensure_ascii=False))
        return 0

    if not settings.smtp_host:
        print(json.dumps({"ok": False, "error": "SMTP not configured"}))
        return 1

    rows, sent, failed = [], 0, []
    server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=45)
    try:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        for i, r in enumerate(todo):
            email, name = r["email"].strip(), r["name"].strip()
            try:
                server.send_message(build(email, name, args.subject, html, text))
                sent += 1
                rows.append({"sent_at": datetime.now(UTC).isoformat(timespec="seconds"),
                             "tag": TAG, "email": email, "name": name,
                             "status": "ok", "detail": ""})
            except Exception as exc:  # noqa: BLE001
                failed.append(email)
                rows.append({"sent_at": datetime.now(UTC).isoformat(timespec="seconds"),
                             "tag": TAG, "email": email, "name": name,
                             "status": "fail", "detail": f"{type(exc).__name__}: {exc}"[:200]})
            if i < len(todo) - 1:
                time.sleep(args.delay)
    finally:
        try:
            server.quit()
        except Exception:  # noqa: BLE001
            pass

    _log(rows)
    print(json.dumps({"ok": not failed, "sent": sent, "failed": failed,
                      "skipped": skipped, "log": str(LOG),
                      "subject": args.subject}, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    _guard_check("send_paverifikuar_email")
    sys.exit(main())
