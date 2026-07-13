"""OAK lawyer outreach campaign — safe daily batches from the owner's Gmail.

Reads data/oak_registry.csv (built by scrape_oak_registry.py), sends a small
personalized batch per run, and appends every send to
data/oak_outreach_log.csv so nobody is ever emailed twice.

Deliberately conservative: default 30/run with 8s spacing, because the same
Gmail account also delivers the platform's transactional email (verify
links) — its sender reputation must stay clean.

Usage:
    python scripts/oak_outreach_campaign.py --dry-run     # preview batch
    python scripts/oak_outreach_campaign.py               # send batch of 30
    python scripts/oak_outreach_campaign.py --limit 50    # custom batch size
"""
import csv
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
LOG = DATA / "oak_outreach_log.csv"

DRY_RUN = "--dry-run" in sys.argv
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 30
SEND_DELAY_S = 8

# Never cold-email people already in touch with the platform.
SUPPRESS = {
    "marigonagashi.law@gmail.com",
    "jetons284@gmail.com",
    "kujtim.gacaferri@gmail.com",
    "arifi.arber@gmail.com",
}

# Prishtinë first (most posted cases are there), then the other regions.
REGION_PRIORITY = ["Prishtinë", "Pejë", "Prizren", "Gjilan",
                   "Mitrovicë", "Ferizaj", "Gjakovë"]

SUBJECT = "AvokatIM — platforma kosovare që ju sjell klientë dhe ju kursen kohë"

BODY = """\
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


def load_sent() -> set[str]:
    if not LOG.exists():
        return set()
    with LOG.open(encoding="utf-8") as f:
        return {row["email"] for row in csv.DictReader(f)}


def log_send(row: dict) -> None:
    new_file = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["email", "name", "region", "sent_at"])
        if new_file:
            w.writeheader()
        w.writerow({"email": row["email"], "name": row["name"],
                    "region": row["region"],
                    "sent_at": datetime.now(UTC).isoformat(timespec="seconds")})


def main() -> None:
    with REGISTRY.open(encoding="utf-8") as f:
        registry = [r for r in csv.DictReader(f) if "@" in r["email"]]
    sent = load_sent()

    def prio(r: dict) -> int:
        try:
            return REGION_PRIORITY.index(r["region"])
        except ValueError:
            return len(REGION_PRIORITY)

    pending = [r for r in registry
               if r["email"] not in sent and r["email"] not in SUPPRESS]
    pending.sort(key=prio)
    batch = pending[:LIMIT]
    print(f"registry: {len(registry)} | sent so far: {len(sent)} | "
          f"pending: {len(pending)} | this batch: {len(batch)}\n")

    smtp = None
    if not DRY_RUN:
        smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)

    for i, row in enumerate(batch, 1):
        region_line = f" dhe qytetin ({row['city']})" if row.get("city") else ""
        body = BODY.format(name=row["name"], region_line=region_line)
        if DRY_RUN:
            print(f"[dry-run] {i:>3}. {row['name']} <{row['email']}> ({row['region']})")
            continue
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = SUBJECT
        msg["From"] = formataddr(("Arbër Arifi", settings.smtp_user))
        msg["To"] = row["email"]
        msg["Reply-To"] = settings.smtp_user
        try:
            smtp.sendmail(settings.smtp_user, [row["email"]], msg.as_string())
            log_send(row)
            print(f"{i:>3}. sent to {row['name']} <{row['email']}>")
        except smtplib.SMTPRecipientsRefused:
            log_send(row)  # log anyway so we never retry a dead address
            print(f"{i:>3}. REFUSED {row['email']}")
        except smtplib.SMTPException as exc:
            print(f"{i:>3}. ERROR {row['email']}: {exc} — stopping batch")
            break
        time.sleep(SEND_DELAY_S)

    if smtp is not None:
        smtp.quit()
    print("\nbatch done")


main()
