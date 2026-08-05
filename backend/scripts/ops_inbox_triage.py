"""Read-only triage of the operator's Gmail inbox for the OpenClaw assistant.

Runs from an OpenClaw cron job every ~10 minutes. Fetches messages newer than
the last seen UID with BODY.PEEK (never marks anything read, never deletes),
classifies them and prints a JSON report to stdout:

- "company": reply from a domain in data/de_companies.csv (Track A — the M&A/
            licensing outreach to German legal-tech companies). Escalated
            FIRST with full context; the assistant NEVER answers these
            autonomously — always a draft + PO/JO from the owner. The replying
            domain is recorded in data/de_company_replies.txt so
            de_company_outreach.py stops follow-ups.
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
# Opt-out signals in a reply to outreach — German (UWG-safe) + Albanian +
# English. A bare "STOP" (the phrase our letters advertise) counts too.
OPTOUT_RE = re.compile(
    r"\b(stop|unsubscribe|abbestellen|abmelden|austragen|keine\s+werbung|"
    r"nicht\s+kontaktieren|keine\s+e-?mails?|c[ë|e]rregjistro|hiqmani?|"
    r"mos\s+m[ë|e]\s+shkruani?|remove\s+me|opt[\s-]?out)\b",
    re.IGNORECASE,
)
# Suppression ledger shared by both outreach campaigns (DE + XK read it).
SUPPRESS_LEDGER = PROJECT_DIR / "data" / "de_suppress.txt"
# Track A (company M&A outreach): target list + replied-domain ledger.
COMPANIES_CSV = PROJECT_DIR / "data" / "de_companies.csv"
COMPANY_REPLIES = PROJECT_DIR / "data" / "de_company_replies.txt"
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


def _company_domains() -> dict[str, str]:
    """domain -> company name from the Track A target list (empty if absent)."""
    if not COMPANIES_CSV.exists():
        return {}
    import csv

    with COMPANIES_CSV.open(encoding="utf-8") as f:
        return {r["domain"].strip().lower(): r["company"]
                for r in csv.DictReader(f) if r.get("domain")}


def _match_company(addr: str, domains: dict[str, str]) -> tuple[str, str] | None:
    """(target domain, company name) when the sender's domain is (a subdomain
    of) a Track A target. The TARGET domain (not the raw sender domain) is what
    the reply ledger stores, so subdomain replies still stop follow-ups."""
    dom = addr.rsplit("@", 1)[-1].lower() if "@" in addr else ""
    while dom:
        if dom in domains:
            return dom, domains[dom]
        dom = dom.partition(".")[2] if "." in dom else ""
    return None


def _record_company_reply(domain: str) -> None:
    """Remember that a Track A company answered (dedup) so the outreach tool
    never sends them a follow-up nudge."""
    domain = (domain or "").strip().lower()
    if not domain:
        return
    existing: set[str] = set()
    if COMPANY_REPLIES.exists():
        existing = {l.strip().lower()
                    for l in COMPANY_REPLIES.read_text(encoding="utf-8").splitlines()
                    if l.strip() and not l.startswith("#")}
    if domain in existing:
        return
    COMPANY_REPLIES.parent.mkdir(parents=True, exist_ok=True)
    new_file = not COMPANY_REPLIES.exists()
    with COMPANY_REPLIES.open("a", encoding="utf-8") as f:
        if new_file:
            f.write("# Domains of Track A companies that replied. Auto-"
                    "maintained by ops_inbox_triage.py; read by "
                    "de_company_outreach.py --followups.\n")
        f.write(f"{domain}\n")


def _classify(from_addr: str, subject: str, body: str = "",
              company_domains: dict[str, str] | None = None) -> str:
    if BOUNCE_FROM_RE.search(from_addr) or BOUNCE_FROM_RE.search(subject):
        return "bounce"
    addr = email.utils.parseaddr(from_addr)[1].lower()
    if addr in _SELF_ADDRESSES:
        return "system"
    # Track A (M&A) companies outrank everything else, including opt-out:
    # even a terse "no interest, stop" from a target company is a signal the
    # owner must see and decide on — never silently suppressed.
    if company_domains and _match_company(addr, company_domains):
        return "company"
    # Opt-out only when the phrase essentially IS the whole reply — never
    # swallow a long human message that merely contains the word "stop"
    # (a false positive would silently drop a hot lead and suppress it
    # forever, which is worse than a missed opt-out the owner reviews by hand).
    head = f"{subject}\n{body}".strip()
    if OPTOUT_RE.search(head) and len(head) <= 80:
        return "optout"
    return "human"


def _record_optout(addr: str) -> bool:
    """Append an address to the shared suppression ledger (dedup). Returns
    True when newly added. Both outreach campaigns read this file, so a STOP
    silences all future cold mail everywhere."""
    addr = (addr or "").strip().lower()
    if "@" not in addr:
        return False
    existing: set[str] = set()
    if SUPPRESS_LEDGER.exists():
        for line in SUPPRESS_LEDGER.read_text(encoding="utf-8").splitlines():
            s = line.strip().lower()
            if s and not s.startswith("#"):
                existing.add(s)
    if addr in existing:
        return False
    SUPPRESS_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    new_file = not SUPPRESS_LEDGER.exists()
    with SUPPRESS_LEDGER.open("a", encoding="utf-8") as f:
        if new_file:
            f.write("# Outreach opt-outs (STOP replies). Auto-maintained by "
                    "ops_inbox_triage.py. Read by DE + XK campaigns.\n")
        f.write(f"{addr}\n")
    return True


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

        for uid in sorted(uids):
            status, msg_data = imap.uid("FETCH", str(uid), "(BODY.PEEK[])")
            if status != "OK" or not msg_data or msg_data[0] is None:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            from_h = _decode(msg.get("From"))
            subject = _decode(msg.get("Subject"))
            snippet = _body_snippet(msg)
            kind = _classify(from_h, subject, snippet, company_domains)
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
                    "message_id": (msg.get("Message-ID") or "").strip(),
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
                    "snippet": snippet,
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
