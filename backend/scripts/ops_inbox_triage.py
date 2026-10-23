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
- "personal_t1": sender on the owner's PERSONAL allowlist
            (~/.openclaw/state/email_allowlist.json, lane "personal", D-142/
            D-219 2026-10-09) — the only private senders the assistant may
            answer autonomously (act + notify), and only through
            ops_send_reply.py on the primary model. Allowlist unreadable =
            empty (fail-closed -> "unknown"). D-220 gates (gardhet_t1): the
            mail must carry Authentication-Results with dkim=pass aligned to
            the From domain OR spf=pass, and Reply-To (if any) must equal
            From; otherwise the entry is demoted to "unknown" (draft only)
            with the reasons in "t1_gardhet". Missing/unparseable headers =
            demoted (fail-closed).
- "system": notifications sent by AvokatIM itself (From = our own address) —
            counted only; real-time platform events arrive via ops_notify.
- "bounce": mailer-daemon bounces — counted only, surfaced when spiking.

State (last UID per mailbox) lives in data/ops/inbox_state.json so restarts
and reboots never re-report old mail. Exit code is always 0 with valid JSON;
errors are reported inside the JSON ("error" key) to keep the cron quiet.
"""
import csv
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
# Lidhja mekanike me lëndët e firmës (alias +token@) — i njëjti burim i vërtete
# si hygiene/mailbox (2026-09-07, VENDIM I HALIMIT: "human" vetëm me lidhje).
from scripts.ops_mailbox import _is_matter_alias  # noqa: E402

STATE_FILE = PROJECT_DIR / "data" / "ops" / "inbox_state.json"
# Owner's personal allowlist (deny-by-default, maintained via P-## + owner PO;
# ~/scripts/email_allowlist.py is the gate, this is the same file read-only).
PERSONAL_ALLOWLIST = Path.home() / ".openclaw" / "state" / "email_allowlist.json"
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
            # Malformed senders declare bogus charsets ("unknown-8bit");
            # one bad header must never kill the whole triage run.
            try:
                out.append(text.decode(charset or "utf-8", errors="replace"))
            except LookupError:
                out.append(text.decode("utf-8", errors="replace"))
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


def _outreach_contacts() -> set[str]:
    """Adresat që fushatat TONA i kanë kontaktuar të parat (oak/de outreach).

    Lidhje mekanike me firmën: ne u shkruam të parët, përgjigja e tyre është
    biznes i AvokatIM (parity-a D-070 e ruajtur). Fail-open: pa ledger = set
    bosh (dërguesi mbetet "unknown" = draft-only — ana e sigurt).
    """
    contacts: set[str] = set()
    for name in ("oak_outreach_log.csv", "de_outreach_log.csv"):
        p = PROJECT_DIR / "data" / name
        try:
            with p.open(encoding="utf-8") as f:
                rows = csv.reader(f)
                header = next(rows, None)
                idx = 0
                if header and "email" in header:
                    idx = header.index("email")
                for row in rows:
                    if row and "@" in (row[idx] if idx < len(row) else ""):
                        contacts.add(row[idx].strip().lower())
        except OSError:
            continue
    return contacts


def _personal_allowlist() -> set[str]:
    """Lane "personal" of the owner's allowlist: exact addresses + "@domain"
    suffixes, lower-cased. Missing/broken file or allow_all -> EMPTY set
    (fail-closed: nobody gets the autonomous personal lane by accident)."""
    try:
        data = json.loads(PERSONAL_ALLOWLIST.read_text(encoding="utf-8"))
        lane = (data.get("korsite") or {}).get("personal") or {}
        if lane.get("allow_all"):
            return set()
        return {str(h).strip().lower() for h in lane.get("derguesit_e_miratuar", [])
                if str(h).strip() and str(h).strip() != "*"}
    except (OSError, ValueError, AttributeError):
        return set()


def _in_personal_allowlist(addr: str, allow: set[str]) -> bool:
    a = (addr or "").strip().lower()
    if not a or "@" not in a or a in _SELF_ADDRESSES:
        return False  # never auto-answer ourselves / no-reply@avokatiim.ai
    local = a.split("@", 1)[0]
    if local.startswith(("no-reply", "noreply", "do-not-reply", "donotreply")):
        return False  # allowlisted *domain* does not make a bot a person
    return a in allow or any(h.startswith("@") and a.endswith(h) for h in allow)


# --- D-220 gates for the personal_t1 lane (2026-10-09, patch 2 of S3) -------
# Spoofing a From: header is trivial; the allowlist alone would let a forged
# "gareth.jones@jll.com" get an autonomous reply. Before any send the mail
# must prove its origin via the receiving MTA's Authentication-Results
# (Gmail: "mx.google.com; dkim=pass header.i=@jll.com ...; spf=pass ...
# smtp.mailfrom=...") and must not redirect replies to a third party.
_AUTH_HEADERS = ("Authentication-Results", "ARC-Authentication-Results")
_DKIM_PASS_RE = re.compile(r"\bdkim\s*=\s*pass\b([^;]*)", re.I)
_SPF_PASS_RE = re.compile(r"\bspf\s*=\s*pass\b([^;]*)", re.I)
_DMARC_FAIL_RE = re.compile(r"\bdmarc\s*=\s*fail\b", re.I)
_HEADER_DOMAIN_RE = re.compile(r"header\.(?:d|i)\s*=\s*@?([\w.-]+)", re.I)
_MAILFROM_RE = re.compile(r"(?:smtp\.mailfrom|envelope-from)\s*=\s*(?:[^@\s;]*@)?([\w.-]+)|domain of \S+@([\w.-]+)", re.I)


def _domain_aligned(dom: str, from_domain: str) -> bool:
    """Relaxed alignment (RFC 7489 §3.1): same organisational tree."""
    dom, from_domain = dom.strip(".").lower(), from_domain.strip(".").lower()
    return bool(dom) and bool(from_domain) and (
        dom == from_domain or from_domain.endswith("." + dom) or dom.endswith("." + from_domain))


def _dkim_ok(ar: str, from_domain: str) -> bool:
    """dkim=pass counts ONLY when header.d / header.i aligns with the From
    domain — a pass for the spoofer's own domain proves nothing. A pass
    without header.d is not enough either (fail-closed)."""
    for m in _DKIM_PASS_RE.finditer(ar):
        d = _HEADER_DOMAIN_RE.search(m.group(1))
        if d and _domain_aligned(d.group(1), from_domain):
            return True
    return False


def _spf_ok(ar: str, from_domain: str) -> bool:
    """spf=pass counts when smtp.mailfrom (if stated) aligns with From; a
    bare spf=pass without any envelope info is accepted (D-220 wording)."""
    for m in _SPF_PASS_RE.finditer(ar):
        e = _MAILFROM_RE.search(m.group(1))
        if e is None:
            return True
        if _domain_aligned(e.group(1) or e.group(2) or "", from_domain):
            return True
    return False


def gardhet_t1(msg: email.message.Message) -> tuple[bool, list[str]]:
    """D-220 mandatory gates for the personal_t1 lane. Pure function of the
    parsed message -> (allowed, reasons). Empty reasons == allowed. Any
    missing header, parse error or exception => NOT allowed (fail-closed);
    the caller demotes the mail to "unknown" (draft-for-approval) and keeps
    the reasons in the report so the assistant/owner can see why."""
    arsyet: list[str] = []
    try:
        from_addr = email.utils.parseaddr(_decode(msg.get("From")))[1].strip().lower()
        if "@" not in from_addr:
            return False, ["from-pa-adrese"]
        from_domain = from_addr.rsplit("@", 1)[1]
        # (1) DKIM/SPF from the receiving MTA
        ars = [str(v) for h in _AUTH_HEADERS for v in (msg.get_all(h) or [])]
        if not ars:
            arsyet.append("auth-results-mungon")
        else:
            dkim = any(_dkim_ok(a, from_domain) for a in ars)
            spf = any(_spf_ok(a, from_domain) for a in ars)
            if not (dkim or spf):
                arsyet.append("dkim/spf-jo-pass")
            if any(_DMARC_FAIL_RE.search(a) for a in ars):
                arsyet.append("dmarc-fail")
        # (2) Reply-To must be absent or identical to From (normalised)
        rt_raw = [_decode(v) for v in (msg.get_all("Reply-To") or []) if str(v).strip()]
        if rt_raw:
            rt = [a.strip().lower() for _, a in email.utils.getaddresses(rt_raw)]
            if not rt or any(a != from_addr for a in rt):
                arsyet.append("reply-to-i-huaj")
    except Exception as exc:  # noqa: BLE001 — fail-closed, never a crash
        arsyet.append(f"gabim:{type(exc).__name__}")
    return (not arsyet), arsyet


def _classify(from_addr: str, subject: str, body: str = "",
              company_domains: dict[str, str] | None = None,
              firm_linked: bool = False,
              personal_allow: set[str] | None = None) -> str:
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
    # 2026-09-07 (VENDIM I HALIMIT, incidenti Solar72): "human" — dhe bashkë me
    # të korsia autonome e përgjigjes — VETËM kur maili lidhet MEKANIKISHT me
    # firmën: (a) alias lënde +token@ (_is_matter_alias), ose (b) dërgues që
    # fushatat tona e kontaktuan të parat (ledger-ët e outreach-it). Gjithçka
    # tjetër është "unknown" = draft-për-miratim, KURRË dërgim autonom.
    # Defaulti i vjetër ("human" për çdo të panjohur) i dha korsinë autonome
    # partnerëve privatë të Kllosha-s (Rene/Oliver, Solar72) — 5 dërgime pa
    # PO, 05–07.09.
    if firm_linked:
        return "human"
    # 2026-10-09 (D-219, E-33 verdict KALON, FP=0 proven): the owner's 22
    # allowlisted private senders get their own lane. Still NOT "human"
    # (that lane is the firm's) — the prompt rule (c1) governs what the
    # assistant may do with "personal_t1".
    if personal_allow and _in_personal_allowlist(addr, personal_allow):
        return "personal_t1"
    return "unknown"


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
        # dërgues pa lidhje mekanike me firmën (2026-09-07): draft-only, kurrë
        # përgjigje autonome — i sjellë me të njëjtat fusha si "human"
        "unknown": [],
        # dërgues të allowlist-it PERSONAL (D-219, 2026-10-09): korsia T1
        # personale — vepro + njofto, vetëm ops_send_reply.py, vetëm model primar
        "personal_t1": [],
        # D-220: allowlisted senders that FAILED gardhet_t1 (DKIM/SPF,
        # Reply-To) — they are listed under "unknown" with "t1_gardhet"
        "personal_t1_gardhet_refuzuar": 0,
        "system_count": 0,
        "bounce_count": 0,
        "optout_count": 0,
        "optouts": [],
    }
    company_domains = _company_domains()
    outreach_contacts = _outreach_contacts()
    personal_allow = _personal_allowlist()

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
            sender_addr = email.utils.parseaddr(from_h)[1].lower()
            kind = _classify(from_h, subject, snippet, company_domains,
                             firm_linked=_is_matter_alias(msg)
                             or sender_addr in outreach_contacts,
                             personal_allow=personal_allow)
            t1_gardhet: dict | None = None
            if kind == "personal_t1":
                # D-220 gates: no proof of origin / foreign Reply-To =>
                # draft-only lane, reasons kept for the report + stderr log.
                lejohet, arsyet = gardhet_t1(msg)
                t1_gardhet = {"lejohet": lejohet, "arsyet": arsyet}
                if not lejohet:
                    kind = "unknown"
                    report["personal_t1_gardhet_refuzuar"] += 1
                    print(f"[inbox-triage] personal_t1 -> unknown (gardhet D-220) uid={uid} "
                          f"from={sender_addr} arsyet={','.join(arsyet)}", file=sys.stderr)
            if (kind in ("human", "unknown", "personal_t1")
                    and len(report["human"]) + len(report["unknown"])
                    + len(report["personal_t1"])
                    >= MAX_HUMAN_PER_RUN):
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
                # "human" (i lidhur me lëndë) te human; "personal_t1" (allowlist
                # personal, D-219) te korsia e vet; "unknown" te bucket-i
                # i vet — draft-only (VENDIM I HALIMIT 2026-09-07).
                hyrja = {
                    "uid": uid,
                    "from": from_h,
                    "reply_to": email.utils.parseaddr(
                        _decode(msg.get("Reply-To") or msg.get("From"))
                    )[1],
                    "subject": subject,
                    "date": _decode(msg.get("Date")),
                    "message_id": str(msg.get("Message-ID") or "").strip(),
                    "snippet": snippet,
                }
                if t1_gardhet is not None:
                    hyrja["t1_gardhet"] = t1_gardhet
                report[kind if kind in ("human", "personal_t1") else "unknown"].append(hyrja)
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
