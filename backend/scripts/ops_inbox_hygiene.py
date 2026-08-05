"""Inbox hygiene snapshot for the operator assistant (Halim) — READ-ONLY.

Gives the daily "Higjiena e inbox-it" line for the morning report: how many
unread are sitting in arifi.arber@gmail.com, how old the oldest one is, and a
rough bucket breakdown so Halim knows whether anything needs attention
(bank/finance) versus pure noise (promotions/notifications).

Never changes a flag — connects read-only and fetches headers with PEEK. The
write side (mark-read / archive / label) stays in ops_mailbox.py, which also
holds the matter-alias firewall. This script only classifies matter-alias
mail into its own bucket so it is never suggested for cleanup.

Usage (prints JSON):
    ops_inbox_hygiene.py                 # full snapshot + ready report_line
    ops_inbox_hygiene.py --max 500       # cap how many unread to classify
"""
import argparse
import email
import email.utils
import imaplib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Reuse the exact credential/decoding/firewall logic from the mailbox tool so
# there is a single source of truth for how we talk to Gmail.
from scripts.ops_mailbox import (  # noqa: E402
    _credentials,
    _decode,
    _is_matter_alias,
)

# Keyword buckets, checked in order. First match wins.
_FINANCE = (
    "raiffeisen", "procredit", "teb", "nlb", "bank", "banka", "binance",
    "blockchain", "paypal", "stripe", "coinbase", "revolut", "wise",
)
_PLATFORM = ("avokatiim", "avokatim", "opshub", "naturalbeauty", "no-reply@avokat")
_NOISE = (
    "tiktok", "shopify", "newsletter", "noreply", "no-reply", "notification",
    "notifications", "mailer", "marketing", "promo", "cursor", "digest",
    "updates", "info@", "news@", "team@",
)


def _bucket(sender: str, subject: str) -> str:
    hay = f"{sender} {subject}".lower()
    if any(k in hay for k in _FINANCE):
        return "financiare"
    if any(k in hay for k in _PLATFORM):
        return "platforma"
    if any(k in hay for k in _NOISE):
        return "reklama"
    return "tjera"


def _fetch_headers(imap: imaplib.IMAP4_SSL, uid: int) -> email.message.Message | None:
    # HEADER only + PEEK: fast and never sets \Seen.
    status, data = imap.uid("FETCH", str(uid), "(BODY.PEEK[HEADER])")
    if status != "OK" or not data or data[0] is None:
        return None
    return email.message_from_bytes(data[0][1])


def snapshot(max_scan: int) -> dict:
    host, port, user, password = _credentials()
    if not user or not password:
        return {"error": "IMAP/SMTP credentials not configured in backend/.env"}

    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(user, password)
    imap.select("INBOX", readonly=True)
    try:
        status, data = imap.uid("SEARCH", None, "UNSEEN")
        uids = [int(u) for u in (data[0].split() if status == "OK" and data and data[0] else [])]
        total = len(uids)

        buckets = {"financiare": 0, "platforma": 0, "personale": 0,
                   "reklama": 0, "tjera": 0, "matter": 0}
        oldest_dt: datetime | None = None
        oldest_info = None
        finance_samples: list[dict] = []

        for uid in sorted(uids, reverse=True)[:max_scan]:
            msg = _fetch_headers(imap, uid)
            if msg is None:
                continue
            if _is_matter_alias(msg):
                buckets["matter"] += 1
                continue
            sender = _decode(msg.get("From"))
            subject = _decode(msg.get("Subject"))
            bucket = _bucket(sender, subject)
            # "tjera" from a plausible human (has a display name, not a bulk
            # sender) is more likely personal-needs-attention.
            if bucket == "tjera" and "<" in sender and "@" in sender:
                bucket = "personale"
            buckets[bucket] += 1
            if bucket == "financiare" and len(finance_samples) < 5:
                finance_samples.append({"uid": uid, "from": sender, "subject": subject})

            date_hdr = msg.get("Date")
            parsed = email.utils.parsedate_to_datetime(date_hdr) if date_hdr else None
            if parsed is not None:
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                if oldest_dt is None or parsed < oldest_dt:
                    oldest_dt = parsed
                    oldest_info = {"uid": uid, "from": sender,
                                   "subject": subject, "date": date_hdr}
    finally:
        imap.logout()

    oldest_age_days = None
    if oldest_dt is not None:
        oldest_age_days = (datetime.now(UTC) - oldest_dt).days

    needs_attention = buckets["financiare"] + buckets["personale"]
    line = (
        f"Higjiena e inbox-it: {total} të palexuar"
        + (f" (më i vjetri {oldest_age_days} ditë)" if oldest_age_days is not None else "")
        + f" — kërkojnë vëmendje: {needs_attention} "
        + f"({buckets['financiare']} financiare, {buckets['personale']} personale); "
        + f"zhurmë: {buckets['reklama']}."
    )

    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "unread_total": total,
        "scanned": min(total, max_scan),
        "buckets": buckets,
        "oldest_unread": oldest_info,
        "oldest_age_days": oldest_age_days,
        "needs_attention": needs_attention,
        "finance_samples": finance_samples,
        "report_line": line,
    }


def main() -> dict:
    ap = argparse.ArgumentParser(description="Inbox hygiene snapshot (read-only)")
    ap.add_argument("--max", type=int, default=500,
                    help="max unread messages to classify")
    args = ap.parse_args()
    return snapshot(args.max)


if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2, default=str))
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
