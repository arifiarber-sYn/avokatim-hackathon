"""Professional outreach campaign — safe daily batches from the owner's Gmail.

Phase 1 (lawyers): reads data/oak_registry.csv (built by scrape_oak_registry.py).
Phase 2 (notaries): when every lawyer has been contacted, automatically switches
to data/notaries.json (built by scrape_onk_registry.py) with a notary-specific
letter.

Every send is appended to data/oak_outreach_log.csv so nobody is ever emailed
twice, and a batch refuses to run twice in the same day — this makes the script
safe to trigger from a systemd timer with Persistent=true (catch-up runs after
a reboot cannot double-send).

Default 25/run with 20-60s random spacing — lowered from 60 on 2026-08-05
(audit D-069): the same personal Gmail account also delivers the platform's
transactional email (verify links), so its sender reputation must stay clean.
Randomised delays look less bot-like to Gmail's rate heuristics. The plan is
to migrate cold outreach to a dedicated sending domain (Resend) entirely.

Guardrails (D-069): honours the halim_guard kill switch (AUTONOMY_HALT) and
appends every real batch to the action audit log.

Usage:
    python scripts/oak_outreach_campaign.py --dry-run     # preview batch
    python scripts/oak_outreach_campaign.py               # send batch of 25
    python scripts/oak_outreach_campaign.py --limit 10    # custom batch size
    python scripts/oak_outreach_campaign.py --force       # ignore daily guard
"""
import asyncio
import csv
import json
import random
import smtplib
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_sender import Sender  # noqa: E402
from app.config import settings  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "data"
REGISTRY = DATA / "oak_registry.csv"
NOTARIES = DATA / "notaries.json"
LOG = DATA / "oak_outreach_log.csv"
# Shared opt-out ledger (STOP replies), auto-maintained by ops_inbox_triage.
# Read by both the DE and XK campaigns so one STOP silences all cold mail.
SUPPRESS_LEDGER = DATA / "de_suppress.txt"

DRY_RUN = "--dry-run" in sys.argv
FORCE = "--force" in sys.argv
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 25
SEND_DELAY_RANGE_S = (20, 60)

HALIM_GUARD = Path.home() / "scripts" / "halim_guard.py"

# Never cold-email people already in touch with the platform (static floor —
# registered users are also excluded dynamically from the database).
SUPPRESS = {
    "marigonagashi.law@gmail.com",
    "jetons284@gmail.com",
    "kujtim.gacaferri@gmail.com",
    "arifi.arber@gmail.com",
}

# Prishtinë first (most posted cases are there), then the other regions.
REGION_PRIORITY = ["Prishtinë", "Pejë", "Prizren", "Gjilan",
                   "Mitrovicë", "Ferizaj", "Gjakovë"]

LAWYER_SUBJECT = "AvokatIM — platforma kosovare që ju sjell klientë dhe ju kursen kohë"

LAWYER_BODY = """\
I/E nderuar Av. {name},

Ju shkruaj personalisht — jam Arbër Arifi, krijuesi i AvokatIM
(https://avokatiim.ai), platforma e parë kosovare që lidh qytetarët me
avokatët e licencuar të OAK-së dhe i jep çdo avokati një zyrë digjitale
të plotë.

Çfarë përfitoni konkretisht:

- Raste të reja nga qytetarët: ata postojnë rastin, ju njoftoheni menjëherë
  kur përputhet me fushën tuaj{region_line} dhe vendosni vetë a ta merrni.
- Zyra digjitale: lëndët, afatet sipas LPK-së me llogaritje automatike,
  dokumentet, faturimi — gjithçka në një vend, edhe në telefon.
- Ava, asistentja juridike me AI mbi ligjet e Kosovës: hulumtim me citime,
  përmirësim shkresash, përmbledhje dokumentesh.
- Konsulta me pagesë online dhe orar rezervimesh, nëse dëshironi.

Viti i parë është plotësisht falas, pa kartelë dhe pa detyrime. Zyrat e para të
verifikuara me licencë OAK marrin shenjën e përhershme "Themelues" në
drejtorinë publike.

Regjistrimi zgjat 2 minuta: https://avokatiim.ai/regjistrohu
Më shumë për avokatët: https://avokatiim.ai/per-avokatet

Adresën tuaj e mora nga regjistri publik i avokatëve në oak-ks.org. Ky është
një njoftim i vetëm profesional — nëse nuk dëshironi të kontaktoheni më,
mjafton të përgjigjeni me "STOP" dhe nuk ju shkruajmë më.

Për çdo pyetje më përgjigjuni direkt në këtë email — ju përgjigjem vetë.

Me respekt,
Arbër Arifi
Krijuesi i AvokatIM · https://avokatiim.ai

P.S. Nëse e hapni nga telefoni dhe faqja nuk shfaqet si duhet, hapeni
direkt në Chrome ose Safari (jo brenda aplikacionit të email-it) — shkruani
avokatiim.ai në shiritin e adresës.
"""

NOTARY_SUBJECT = "AvokatIM — zyra noteriale digjitale me AI dhe termine online"

NOTARY_BODY = """\
I/E nderuar noter/e {name},

Ju shkruaj personalisht — jam Arbër Arifi, krijuesi i AvokatIM
(https://avokatiim.ai), platforma kosovare ku qytetarët gjejnë avokatët
dhe noterët e vendit. Tani AvokatIM ofron edhe zyrën noteriale digjitale.

Çfarë përfitoni konkretisht:

- Ava, asistentja me AI që e njeh Ligjin për Noterinë (06/L-010, me
  plotësimet) dhe tarifat sipas UA 02/2012 — përgjigje me referenca,
  hartim aktesh dhe përmbledhje dokumentesh në sekonda.
- Termine online: qytetarët{region_line} ju gjejnë në drejtorinë publike
  të noterëve (https://avokatiim.ai/noteret) dhe rezervojnë vetë terminin —
  madje vijnë me dosjen e përgatitur paraprakisht, që kurseni kohë në zyrë.
- Lëndët, dokumentet e enkriptuara, kalendari dhe faturimi sipas tarifave
  zyrtare — gjithçka në një vend, edhe në telefon.
- Pa garë rastesh dhe pa vendosje të promovuara: noterët listohen të
  barabartë, siç e kërkon detyra.

Viti i parë është plotësisht falas, pa kartelë dhe pa detyrime.

Regjistrimi zgjat 2 minuta: https://avokatiim.ai/regjistrohu?profesioni=noter
Më shumë për noterët: https://avokatiim.ai/per-noteret

Adresën tuaj e mora nga regjistri publik i noterëve të Kosovës. Ky është
një njoftim i vetëm profesional — nëse nuk dëshironi të kontaktoheni më,
mjafton të përgjigjeni me "STOP" dhe nuk ju shkruajmë më.

Për çdo pyetje më përgjigjuni direkt në këtë email — ju përgjigjem vetë.

Me respekt,
Arbër Arifi
Krijuesi i AvokatIM · https://avokatiim.ai

P.S. Nëse e hapni nga telefoni dhe faqja nuk shfaqet si duhet, hapeni
direkt në Chrome ose Safari (jo brenda aplikacionit të email-it) — shkruani
avokatiim.ai në shiritin e adresës.
"""


def load_log() -> list[dict]:
    if not LOG.exists():
        return []
    with LOG.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sent_today(log_rows: list[dict]) -> bool:
    """True when the log already contains sends from today (local date) —
    the guard that makes Persistent=true catch-up runs safe."""
    today = datetime.now().astimezone().date()
    for row in log_rows:
        try:
            ts = datetime.fromisoformat(row["sent_at"])
        except (KeyError, ValueError):
            continue
        if ts.astimezone().date() == today:
            return True
    return False


def log_send(row: dict, audience: str) -> None:
    new_file = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["email", "name", "region", "sent_at", "audience"],
            extrasaction="ignore",
        )
        if new_file:
            w.writeheader()
        w.writerow({"email": row["email"], "name": row["name"],
                    "region": row.get("region") or row.get("city") or "",
                    "sent_at": datetime.now(UTC).isoformat(timespec="seconds"),
                    "audience": audience})


def ledger_suppressions() -> set[str]:
    """Opt-out addresses (STOP replies) shared across campaigns."""
    if not SUPPRESS_LEDGER.exists():
        return set()
    out: set[str] = set()
    for line in SUPPRESS_LEDGER.read_text(encoding="utf-8").splitlines():
        s = line.strip().lower()
        if s and not s.startswith("#") and "@" in s:
            out.add(s)
    return out


def registered_emails() -> set[str]:
    """Emails of everyone already on the platform (professionals + citizens) —
    they get product emails, never cold outreach."""
    from sqlalchemy import text

    from app.database import SessionLocal

    async def _fetch() -> set[str]:
        async with SessionLocal() as db:
            rows = await db.execute(text(
                "SELECT lower(email) FROM users "
                "UNION SELECT lower(email) FROM citizen_users"
            ))
            return {r[0] for r in rows}

    return asyncio.run(_fetch())


def load_lawyers() -> list[dict]:
    with REGISTRY.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if "@" in r["email"]]

    def prio(r: dict) -> int:
        try:
            return REGION_PRIORITY.index(r["region"])
        except ValueError:
            return len(REGION_PRIORITY)

    rows.sort(key=prio)
    return rows


def load_notaries() -> list[dict]:
    items = json.loads(NOTARIES.read_text(encoding="utf-8"))
    if isinstance(items, dict):
        items = items.get("notaries", [])
    rows = [n for n in items if "@" in (n.get("email") or "")]

    def prio(r: dict) -> int:
        try:
            return REGION_PRIORITY.index(r.get("city", ""))
        except ValueError:
            return len(REGION_PRIORITY)

    rows.sort(key=prio)
    return rows


def _kill_switch_active() -> bool:
    """True when halim_guard says autonomy is halted (exit code 1)."""
    if not HALIM_GUARD.exists():
        return False
    return subprocess.run(
        [sys.executable, str(HALIM_GUARD), "status"],
        capture_output=True,
    ).returncode != 0


def _audit(action: str) -> None:
    """Append the batch to the halim_guard action audit log (best effort)."""
    if not HALIM_GUARD.exists():
        return
    subprocess.run(
        [sys.executable, str(HALIM_GUARD), "audit",
         "--account", "arifi.arber@gmail.com",
         "--action", action, "--result", "ok"],
        capture_output=True,
    )


def main() -> None:
    if not DRY_RUN and _kill_switch_active():
        print("AUTONOMY_HALT active (halim_guard) — refusing to send")
        return

    log_rows = load_log()
    if sent_today(log_rows) and not DRY_RUN and not FORCE:
        print("today's batch already sent — nothing to do (use --force to override)")
        return

    sent = {r["email"].lower() for r in log_rows}
    suppress = {s.lower() for s in SUPPRESS} | ledger_suppressions() | registered_emails()

    def pending(rows: list[dict]) -> list[dict]:
        """Filter out already-sent/suppressed addresses AND duplicates within
        the source list itself (the registry can list one address twice —
        the 2026-07 'Vuksani' double-send incident)."""
        seen_in_batch: set[str] = set()
        out: list[dict] = []
        for r in rows:
            addr = r["email"].lower()
            if addr in sent or addr in suppress or addr in seen_in_batch:
                continue
            seen_in_batch.add(addr)
            out.append(r)
        return out

    lawyers = pending(load_lawyers())
    notaries = pending(load_notaries())

    # Phase 1: lawyers. Phase 2 (automatic): notaries, once lawyers are done.
    if lawyers:
        audience, batch_pool = "lawyer", lawyers
        subject, body_tpl = LAWYER_SUBJECT, LAWYER_BODY
    elif notaries:
        audience, batch_pool = "notary", notaries
        subject, body_tpl = NOTARY_SUBJECT, NOTARY_BODY
    else:
        print("campaign complete — every lawyer and notary has been contacted")
        return

    sender = Sender()
    limit = LIMIT
    if sender.daily_cap is not None and sender.daily_cap < limit:
        limit = sender.daily_cap  # warm-up cap on the fresh Resend domain
        print(f"(warm-up cap active: {limit}/day on the dedicated domain)")
    batch = batch_pool[:limit]
    print(f"audience: {audience} | mode: {sender.mode} | sent so far: {len(sent)} | "
          f"pending lawyers: {len(lawyers)} | pending notaries: {len(notaries)} | "
          f"this batch: {len(batch)}\n")

    sent_count = 0

    for i, row in enumerate(batch, 1):
        city = row.get("city") or ""
        if audience == "lawyer":
            region_line = f" dhe qytetin ({city})" if city else ""
        else:
            region_line = f" e qytetit tuaj ({city})" if city else ""
        body = body_tpl.format(name=row["name"], region_line=region_line)
        if DRY_RUN:
            print(f"[dry-run] {i:>3}. {row['name']} <{row['email']}> "
                  f"({row.get('region') or city})")
            continue
        try:
            # RFC 2369 one-click opt-out; the STOP subject is picked up by
            # ops_inbox_triage which writes the address to de_suppress.txt.
            sender.send(row["email"], subject, body, "Arbër Arifi",
                        f"<mailto:{settings.smtp_user}?subject=STOP>")
            log_send(row, audience)
            sent_count += 1
            print(f"{i:>3}. sent to {row['name']} <{row['email']}>")
        except smtplib.SMTPRecipientsRefused:
            log_send(row, audience)  # log anyway so we never retry a dead address
            print(f"{i:>3}. REFUSED {row['email']}")
        except (smtplib.SMTPException, RuntimeError) as exc:
            print(f"{i:>3}. ERROR {row['email']}: {exc} — stopping batch")
            break
        time.sleep(random.uniform(*SEND_DELAY_RANGE_S))

    sender.close()
    if not DRY_RUN and sent_count:
        _audit(f"oak outreach batch: {sent_count} emails ({audience}, "
               f"mode={sender.mode})")
    print("\nbatch done")


if __name__ == "__main__":
    main()
