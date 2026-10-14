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
    ops_inbox_hygiene.py --seen-hours 48 # also list SEEN mail of the last 48 h (default; 0 = UNSEEN only)

SEEN window (S24, 2026-10-09, audit "Halimi vs fronti" E4): the triage used to
see only UNSEEN, so anything the owner opened on his phone vanished for the
assistant before it was triaged. The search is now `(OR UNSEEN SINCE <48 h>)`;
UNSEEN semantics (counts, buckets, report_line) are unchanged, and the SEEN
messages are surfaced separately in `seen_recent` with a per-uid `drafted`
flag read from ~/.openclaw/state/t2_draft_index.json (t2_draft_gate.py), so a
SEEN mail that already has a T2 draft is never drafted twice.
"""
import argparse
import email
import email.utils
import imaplib
import json
import re
import sys
from datetime import UTC, datetime, timedelta
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
    "updates", "info@", "news@", "team@", "chess", "devpost",
    # Alibaba marketplace notifications (sekretari handoff 2026-10-13:
    # "feedback@service.alibaba.com" — "New seller message..." — had no
    # _NOISE keyword and an unknown local part, so it was promoted to
    # "personale" and inflated "kërkojnë vëmendje" (1/1 that morning).
    "alibaba",
    # Meta hackathon bulk mail (sekretari handoffs 2026-10-13T191200Z +
    # 2026-10-14T062139Z: "AI at Meta <update@digital.metamail.com>" — "It's go
    # time: Apply..." — local part "update" is not in _BULK_LOCAL and the domain
    # "digital.metamail.com" escaped _BULK_DOMAIN, so it was promoted to
    # "personale" and inflated "kërkojnë vëmendje" (1/1). Substring token is
    # robust to metamail subdomains.)
    "metamail",
)

# Bulk-sender local parts: a display name alone does NOT make a sender
# human (sekretari handoff 2026-09-24: chess.com streaks@/hello@ were
# promoted to "personale" and polluted the morning "kërkojnë vëmendje").
_BULK_LOCAL = (
    "streaks", "hello", "welcome", "alerts", "receipts", "no-reply",
    "noreply", "notifications", "notification", "friendsuggestion",
)

# Bulk/marketing domains + ESP subdomain prefixes: the LOCAL part alone is not
# enough. (sekretari handoff 2026-10-05: "canvadesignschool@engage.canva.com"
# had an unknown local part and no _NOISE keyword, so it was promoted to
# "personale"; the domain is clearly a marketing/ESP subdomain.) Conservative:
# exact known domains + clear ESP subdomain prefixes only.
_BULK_DOMAIN = (
    "canva.com", "engage.canva.com", "mailchimp.com", "sendgrid.net",
    "hubspot.com", "constantcontact.com", "klaviyo.com", "mailgun.org",
    "postmarkapp.com", "substack.com", "beehiiv.com", "mailerlite.com",
    "campaign-archive.com", "cmail19.com", "cmail20.com",
    # Meta/Facebook bulk notifications (sekretari handoff 2026-10-08:
    # "Facebook Friend Suggestions <friendsuggestion@facebookmail.com>"
    # escaped _NOISE and promoted to "personale" -> inflated needs_attention).
    "facebookmail.com",
    # Monitoring notifications (sekretari handoff 2026-10-11: "Healthchecks.io
    # <healthchecks.io@healthchecks.io>" UP/DOWN alerts for halim-dead-man had
    # no _NOISE keyword and an unknown local part, so 2 of 4 that morning were
    # promoted to "personale" -> inflated needs_attention).
    "healthchecks.io",
)
_BULK_DOMAIN_PREFIX = (
    "engage.", "email.", "mail.", "news.", "marketing.", "notify.",
    "notifications.", "info.", "em.", "e2.", "cmail",
)


def _is_bulk_domain_prefix(dom: str) -> bool:
    """ESP subdomain-prefix match, tolerant of numeric variants (em1., mail2.).

    sekretari handoff 2026-10-06: "Cloudflare <em@em1.cloudflare.com>"
    (marketing) escaped the literal "em." prefix, was promoted to "personale"
    and inflated "needs_attention". Strip trailing digits from the leading
    label and retry against _BULK_DOMAIN_PREFIX so em1./em2./em3. -> "em.",
    mail2. -> "mail.", etc. all resolve as bulk.
    """
    if any(dom.startswith(p) for p in _BULK_DOMAIN_PREFIX):
        return True
    label = dom.split(".", 1)[0].rstrip("0123456789")
    return bool(label) and f"{label}." in _BULK_DOMAIN_PREFIX

# Canonical bucket -> T-class mapping (RAPORTIMI.md §"Mapimi i bucket-eve", D-142).
# Authoritative, machine-readable source for the triage ledger line so the loop
# never re-derives it from model memory (recurred 03.10 T3 / 04.10 T0 / 05.10 T0 —
# handoffs 2026-10-03T184950Z, 20261004-190032, 2026-10-05T012027Z).
BUCKET_TO_T = {
    "reklama": "T0",
    "tjera": "T0",
    "platforma": "T1",
    "financiare": "T1/T2",  # email_allowlist.py: LEJOHET -> T1, REFUZOHET -> T2
    "personale": "T1/T2",
    "matter": "MOS-PREK",
}


def _local_part(sender: str) -> str:
    addr = sender.split("<")[-1].split(">")[0].strip()
    return addr.rsplit("@", 1)[0].lower()


def _domain(sender: str) -> str:
    addr = sender.split("<")[-1].split(">")[0].strip()
    return addr.rsplit("@", 1)[-1].lower() if "@" in addr else ""


def _bucket(sender: str, subject: str) -> str:
    hay = f"{sender} {subject}".lower()
    if any(k in hay for k in _FINANCE):
        return "financiare"
    if any(k in hay for k in _PLATFORM):
        return "platforma"
    if any(k in hay for k in _NOISE):
        return "reklama"
    return "tjera"


def _final_bucket(sender: str, subject: str) -> str:
    bucket = _bucket(sender, subject)
    # "tjera" from a plausible human (has a display name, not a bulk
    # sender) is more likely personal-needs-attention.
    if bucket == "tjera" and "<" in sender and "@" in sender:
        local = _local_part(sender)
        dom = _domain(sender)
        if (not any(k in local for k in _BULK_LOCAL)
                and dom not in _BULK_DOMAIN
                and not _is_bulk_domain_prefix(dom)):
            bucket = "personale"
    return bucket


# T2 draft dedup index maintained by ~/scripts/t2_draft_gate.py (uid -> files).
# Read-only here: a SEEN mail that already has a draft must not be re-drafted.
T2_DRAFT_INDEX = Path.home() / ".openclaw" / "state" / "t2_draft_index.json"
_FLAGS_RE = re.compile(rb"FLAGS \(([^)]*)\)")


def _search_criteria(seen_hours: int, now: datetime | None = None) -> str:
    """IMAP SEARCH criteria: UNSEEN only when seen_hours == 0, otherwise
    `(OR UNSEEN SINCE dd-Mon-yyyy)` — UNSEEN of any age plus everything (SEEN
    included) received in the last `seen_hours`. SINCE is date-granular, so
    the window is rounded down to the start of that day (never narrower)."""
    if seen_hours <= 0:
        return "UNSEEN"
    now = now or datetime.now(UTC)
    since = (now - timedelta(hours=seen_hours)).strftime("%d-%b-%Y")
    return f"(OR UNSEEN SINCE {since})"


def _drafted_uids() -> set[str]:
    """uids that already have a T2 draft (t2_draft_gate index). Missing/broken
    index -> empty set (fail-open: the LLM still runs `t2_draft_gate.py check`)."""
    try:
        data = json.loads(T2_DRAFT_INDEX.read_text(encoding="utf-8"))
        return {str(k) for k in data} if isinstance(data, dict) else set()
    except (OSError, ValueError):
        return set()


def _fetch_headers(imap: imaplib.IMAP4_SSL, uid: int) -> tuple[email.message.Message | None, bool]:
    # HEADER only + PEEK: fast and never sets \Seen. FLAGS ride along so the
    # SEEN state is known without a second round-trip.
    status, data = imap.uid("FETCH", str(uid), "(FLAGS BODY.PEEK[HEADER])")
    if status != "OK" or not data or data[0] is None:
        return None, False
    meta = data[0][0] if isinstance(data[0], tuple) else b""
    m = _FLAGS_RE.search(meta or b"")
    seen = b"\\Seen" in (m.group(1) if m else b"")
    return email.message_from_bytes(data[0][1]), seen


def snapshot(max_scan: int, seen_hours: int = 48) -> dict:
    host, port, user, password = _credentials()
    if not user or not password:
        return {"error": "IMAP/SMTP credentials not configured in backend/.env"}

    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(user, password)
    imap.select("INBOX", readonly=True)
    try:
        status, data = imap.uid("SEARCH", None, _search_criteria(seen_hours))
        uids = [int(u) for u in (data[0].split() if status == "OK" and data and data[0] else [])]

        buckets = {"financiare": 0, "platforma": 0, "personale": 0,
                   "reklama": 0, "tjera": 0, "matter": 0}
        oldest_dt: datetime | None = None
        oldest_info = None
        finance_samples: list[dict] = []
        # SEEN mail of the window: listed, never counted in the UNSEEN stats.
        drafted = _drafted_uids()
        seen_recent: list[dict] = []
        seen_uids: set[int] = set()

        for uid in sorted(uids, reverse=True)[:max_scan]:
            msg, is_seen = _fetch_headers(imap, uid)
            if msg is None:
                continue
            if _is_matter_alias(msg):
                if not is_seen:
                    buckets["matter"] += 1
                continue
            sender = _decode(msg.get("From"))
            subject = _decode(msg.get("Subject"))
            bucket = _final_bucket(sender, subject)
            if is_seen:
                seen_uids.add(uid)
                seen_recent.append({"uid": uid, "from": sender, "subject": subject,
                                    "bucket": bucket, "t": BUCKET_TO_T.get(bucket),
                                    "drafted": str(uid) in drafted})
                continue
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

    # UNSEEN semantics unchanged: total/scanned count only unread mail.
    total = len(uids) - len(seen_uids)

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
        "bucket_to_t": BUCKET_TO_T,
        "t_counts": {
            "t0": buckets["reklama"] + buckets["tjera"],
            "t1": buckets["platforma"],
            "t2": 0,
            "t_allowlist_pending": buckets["financiare"] + buckets["personale"],
            "matter": buckets["matter"],
        },
        "t_counts_note": (
            "t0/t1/t2 are definitive when t_allowlist_pending == 0; otherwise "
            "resolve financiare/personale via email_allowlist.py (LEJOHET->T1, "
            "REFUZOHET->T2) per RAPORTIMI.md. Source: RAPORTIMI.md mapping, D-142."
        ),
        "oldest_unread": oldest_info,
        "oldest_age_days": oldest_age_days,
        "needs_attention": needs_attention,
        "finance_samples": finance_samples,
        "report_line": line,
        # S24: SEEN mail of the last `seen_hours` (owner opened it) — triage
        # still evaluates it (R-axis / T2), but `drafted: true` = draft exists,
        # skip. Before drafting any of these: `t2_draft_gate.py check --uid`.
        "seen_hours": seen_hours,
        "seen_recent_total": len(seen_recent),
        "seen_recent_undrafted": sum(1 for s in seen_recent if not s["drafted"]),
        "seen_recent": seen_recent[:50],
    }


def main() -> dict:
    ap = argparse.ArgumentParser(description="Inbox hygiene snapshot (read-only)")
    ap.add_argument("--max", type=int, default=500,
                    help="max unread messages to classify")
    ap.add_argument("--seen-hours", type=int, default=48,
                    help="also list SEEN mail newer than N hours (0 = UNSEEN only, old behaviour)")
    args = ap.parse_args()
    return snapshot(args.max, args.seen_hours)


if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2, default=str))
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
