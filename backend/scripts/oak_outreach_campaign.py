"""Professional outreach campaign — safe daily batches from the owner's Gmail.

Phase 1 (lawyers): reads data/oak_registry.csv (built by scrape_oak_registry.py).
Phase 2 (notaries): when every lawyer has been contacted, automatically switches
to data/notaries.json (built by scrape_onk_registry.py) with a notary-specific
letter.

Every send is appended to data/oak_outreach_log.csv so nobody is ever emailed
twice, and a batch refuses to run twice in the same day — this makes the script
safe to trigger from a systemd timer with Persistent=true (catch-up runs after
a reboot cannot double-send).

Deliberately conservative: default 30/run with 8s spacing, because the same
Gmail account also delivers the platform's transactional email (verify
links) — its sender reputation must stay clean.

Usage:
    python scripts/oak_outreach_campaign.py --dry-run     # preview batch
    python scripts/oak_outreach_campaign.py               # send batch of 30
    python scripts/oak_outreach_campaign.py --limit 50    # custom batch size
    python scripts/oak_outreach_campaign.py --force       # ignore daily guard
"""
import asyncio
import csv
import json
import smtplib
import sys
import time
from datetime import UTC, datetime
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "data"
REGISTRY = DATA / "oak_registry.csv"
NOTARIES = DATA / "notaries.json"
LOG = DATA / "oak_outreach_log.csv"

DRY_RUN = "--dry-run" in sys.argv
FORCE = "--force" in sys.argv
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 30
SEND_DELAY_S = 8

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

Tre muajt e parë janë falas, pa kartelë dhe pa detyrime. Zyrat e para të
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

Tre muajt e parë janë falas, pa kartelë dhe pa detyrime.

Regjistrimi zgjat 2 minuta: https://avokatiim.ai/regjistrohu?profesioni=noter
Më shumë për noterët: https://avokatiim.ai/per-noteret

Adresën tuaj e mora nga regjistri publik i noterëve të Kosovës. Ky është
një njoftim i vetëm profesional — nëse nuk dëshironi të kontaktoheni më,
mjafton të përgjigjeni me "STOP" dhe nuk ju shkruajmë më.

Për çdo pyetje më përgjigjuni direkt në këtë email — ju përgjigjem vetë.

Me respekt,
Arbër Arifi
Krijuesi i AvokatIM · https://avokatiim.ai
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


def main() -> None:
    log_rows = load_log()
    if sent_today(log_rows) and not DRY_RUN and not FORCE:
        print("today's batch already sent — nothing to do (use --force to override)")
        return

    sent = {r["email"].lower() for r in log_rows}
    suppress = {s.lower() for s in SUPPRESS} | registered_emails()

    def pending(rows: list[dict]) -> list[dict]:
        return [r for r in rows
                if r["email"].lower() not in sent
                and r["email"].lower() not in suppress]

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

    batch = batch_pool[:LIMIT]
    print(f"audience: {audience} | sent so far: {len(sent)} | "
          f"pending lawyers: {len(lawyers)} | pending notaries: {len(notaries)} | "
          f"this batch: {len(batch)}\n")

    smtp = None
    if not DRY_RUN:
        smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)

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
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr(("Arbër Arifi", settings.smtp_user))
        msg["To"] = row["email"]
        msg["Reply-To"] = settings.smtp_user
        try:
            smtp.sendmail(settings.smtp_user, [row["email"]], msg.as_string())
            log_send(row, audience)
            print(f"{i:>3}. sent to {row['name']} <{row['email']}>")
        except smtplib.SMTPRecipientsRefused:
            log_send(row, audience)  # log anyway so we never retry a dead address
            print(f"{i:>3}. REFUSED {row['email']}")
        except smtplib.SMTPException as exc:
            print(f"{i:>3}. ERROR {row['email']}: {exc} — stopping batch")
            break
        time.sleep(SEND_DELAY_S)

    if smtp is not None:
        smtp.quit()
    print("\nbatch done")


if __name__ == "__main__":
    main()
