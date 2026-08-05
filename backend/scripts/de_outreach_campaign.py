"""Ava Legal — German lawyer outreach (Track B), safe daily batches.

Mirror of oak_outreach_campaign.py, adapted for Germany:

- Reads data/de_lawyers.csv (built by scrape_de_lawyers.py).
- Sends the "Gründungspartner" letter in GERMAN, signed "Arbër Arifi ·
  Ava Legal", linking only to https://de.avokatiim.ai — never AvokatIM /
  Kosovo (brand split, DECISIONS D-056).
- Every send is appended to data/de_outreach_log.csv (never email twice)
  and a batch refuses to run twice the same day, so it is safe under a
  systemd timer with Persistent=true.
- Suppression = already-registered platform users (DB) + data/de_suppress.txt
  (opt-outs, maintained automatically by ops_inbox_triage) + a static set.

Volume is deliberately LOW (15/day, 10s apart): the sending Gmail account
also carries transactional mail, and cold B2B email in Germany is a legal
grey zone (UWG §7) — a small, polite, clearly-opt-out-able trickle keeps
both sender reputation and legal exposure minimal. Raise only after weeks
without complaints (see docs/pitch/strategjia-tregu-gjerman.txt).

TRACK B IS PAUSED (audit D-069, 2026-08-05): because of the UWG §7 grey
zone, real sends refuse to run unless the environment explicitly sets
DE_TRACK_B_ENABLE=1. --dry-run always works. Do NOT set that variable in
any timer/cron without the owner's explicit decision.

Usage:
    python scripts/de_outreach_campaign.py --dry-run   # preview batch
    DE_TRACK_B_ENABLE=1 python scripts/de_outreach_campaign.py  # send batch
    python scripts/de_outreach_campaign.py --limit 10  # custom size
    python scripts/de_outreach_campaign.py --force     # ignore daily guard
"""
import asyncio
import csv
import os
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
REGISTRY = DATA / "de_lawyers.csv"
LOG = DATA / "de_outreach_log.csv"
SUPPRESS_FILE = DATA / "de_suppress.txt"

DRY_RUN = "--dry-run" in sys.argv
FORCE = "--force" in sys.argv
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 15
SEND_DELAY_S = 10

HALIM_GUARD = Path.home() / "scripts" / "halim_guard.py"

# Static floor of never-contact addresses (owner's own, partners, press).
SUPPRESS = {
    "arifi.arber@gmail.com",
}

SUBJECT = "Ihre Kanzlei nimmt Mandate an, während Sie schlafen — Ava Legal"

# {anrede_line} is a full salutation line; {area_line} is optional and may be "".
BODY = """\
{anrede_line}

ich schreibe Ihnen persönlich — mein Name ist Arbër Arifi, ich bin der
Gründer von Ava Legal (https://de.avokatiim.ai), einer neuen
Kanzleisoftware, bei der die KI nicht ein Zusatzmodul ist, sondern das
Fundament.

Was Ava Legal für Ihre Kanzlei konkret leistet:

- Mandantenaufnahme rund um die Uhr — über Web, WhatsApp und Telefon.
  Eine KI-Rezeption nimmt strukturiert auf, worum es geht, und legt eine
  fertige Fallanfrage an, auch nachts und am Wochenende.
- Fristen nach ZPO, ArbGG und VwGO mit automatischer Berechnung,
  RVG-Abrechnung, E-Rechnung (ZUGFeRD/XRechnung, DATEV-Export) und
  Mahnwesen — die tägliche Kanzleiorganisation an einem Ort, auch mobil.
- Ein KI-Assistent, der deutsches Recht und über 16.000
  Gerichtsentscheidungen zitiert und jedes Zitat automatisch gegen den
  Korpus verifiziert — Sie sehen sofort, was belegt ist.
{area_line}
Für die ersten fünf Kanzleien in Deutschland: 12 Monate kostenlos,
Datenmigration aus RA-MICRO oder Advoware inklusive, danach eine
Preisgarantie von 39 €/Nutzer/Monat. Im Gegenzug wünschen wir uns nur
ehrliches Feedback und — wenn Sie zufrieden sind — eine Referenz.

Testen können Sie sofort selbst: https://de.avokatiim.ai
Gern zeige ich Ihnen alles in rund 20 Minuten per Video-Call.

Ihre Adresse stammt aus dem öffentlichen Anwaltsverzeichnis der
Anwaltauskunft (anwaltauskunft.de). Dies ist eine einmalige,
professionelle Kontaktaufnahme — möchten Sie nicht kontaktiert werden,
genügt eine Antwort mit "STOP", und Sie hören nie wieder von uns.

Für Fragen antworten Sie einfach direkt auf diese E-Mail — Sie erreichen
mich persönlich.

Mit freundlichen Grüßen
Arbër Arifi
Gründer · Ava Legal · https://de.avokatiim.ai
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


def log_send(row: dict) -> None:
    new_file = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["email", "name", "city", "sent_at"],
            extrasaction="ignore",
        )
        if new_file:
            w.writeheader()
        name = f"{row.get('vorname', '')} {row.get('nachname', '')}".strip()
        w.writerow({"email": row["email"], "name": name,
                    "city": row.get("city", ""),
                    "sent_at": datetime.now(UTC).isoformat(timespec="seconds")})


def file_suppressions() -> set[str]:
    if not SUPPRESS_FILE.exists():
        return set()
    out: set[str] = set()
    for line in SUPPRESS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip().lower()
        if line and not line.startswith("#") and "@" in line:
            out.add(line)
    return out


def registered_emails() -> set[str]:
    """Emails of everyone already on the platform — never cold outreach."""
    from sqlalchemy import text

    from app.database import SessionLocal

    async def _fetch() -> set[str]:
        async with SessionLocal() as db:
            rows = await db.execute(text(
                "SELECT lower(email) FROM users "
                "UNION SELECT lower(email) FROM citizen_users"
            ))
            return {r[0] for r in rows}

    try:
        return asyncio.run(_fetch())
    except Exception as exc:  # noqa: BLE001 — DB optional for --dry-run
        print(f"(warning: could not read registered emails: {exc})")
        return set()


def load_lawyers() -> list[dict]:
    with REGISTRY.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if "@" in (r.get("email") or "")]

    def prio(r: dict) -> int:
        try:
            return -int(r.get("alb_score") or 0)
        except ValueError:
            return 0

    rows.sort(key=prio)
    return rows


def salutation(row: dict) -> str:
    anrede = (row.get("anrede") or "").strip()
    titel = (row.get("titel") or "").strip()
    last = (row.get("nachname") or "").strip()
    if anrede and last:
        person = f"{anrede} {titel} {last}".replace("  ", " ").strip()
        prefix = "Sehr geehrte" if anrede == "Frau" else "Sehr geehrter"
        return f"{prefix} {person},"
    return "Sehr geehrte Damen und Herren,"


def area_line(row: dict) -> str:
    areas = (row.get("rechtsgebiete") or "").split(";")
    first = areas[0].strip() if areas else ""
    if not first:
        return ""
    return (
        f"- Gerade im {first} kommen viele Mandate über Erstkontakte "
        f"außerhalb der Bürozeiten — genau diese fängt Ava Legal für Sie auf.\n"
    )


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
    if not DRY_RUN and os.environ.get("DE_TRACK_B_ENABLE") != "1":
        print("Track B (avokatët gjermanë) është PAUSED (UWG §7, D-069). "
              "Dërgimi real kërkon DE_TRACK_B_ENABLE=1 — vendos vetëm me "
              "vendim eksplicit të Kllosha-s. --dry-run punon gjithmonë.")
        return
    if not DRY_RUN and _kill_switch_active():
        print("AUTONOMY_HALT active (halim_guard) — refusing to send")
        return

    if not REGISTRY.exists():
        print(f"no registry at {REGISTRY} — run scrape_de_lawyers.py first")
        return

    log_rows = load_log()
    if sent_today(log_rows) and not DRY_RUN and not FORCE:
        print("today's batch already sent — nothing to do (use --force to override)")
        return

    sent = {r["email"].lower() for r in log_rows}
    suppress = {s.lower() for s in SUPPRESS} | file_suppressions() | registered_emails()

    pending = [r for r in load_lawyers()
               if r["email"].lower() not in sent
               and r["email"].lower() not in suppress]

    if not pending:
        print("campaign complete — every harvested lawyer has been contacted")
        return

    sender = Sender()
    limit = LIMIT
    if sender.daily_cap is not None and sender.daily_cap < limit:
        limit = sender.daily_cap  # warm-up cap on the fresh Resend domain
        print(f"(warm-up cap active: {limit}/day on the dedicated domain)")
    batch = pending[:limit]
    print(f"mode: {sender.mode} | sent so far: {len(sent)} | "
          f"pending: {len(pending)} | this batch: {len(batch)}\n")

    sent_count = 0

    for i, row in enumerate(batch, 1):
        body = BODY.format(anrede_line=salutation(row), area_line=area_line(row))
        name = f"{row.get('vorname', '')} {row.get('nachname', '')}".strip()
        if DRY_RUN:
            print(f"[dry-run] {i:>3}. {name or '(Kanzlei)'} <{row['email']}> "
                  f"({row.get('city')}) alb={row.get('alb_score')}")
            continue
        try:
            # RFC 2369 one-click opt-out; the STOP subject is picked up by
            # ops_inbox_triage which writes the address to de_suppress.txt.
            sender.send(row["email"], SUBJECT, body, "Arbër Arifi · Ava Legal",
                        f"<mailto:{settings.smtp_user}?subject=STOP>")
            log_send(row)
            sent_count += 1
            print(f"{i:>3}. sent to {name} <{row['email']}>")
        except smtplib.SMTPRecipientsRefused:
            log_send(row)  # log anyway so we never retry a dead address
            print(f"{i:>3}. REFUSED {row['email']}")
        except (smtplib.SMTPException, RuntimeError) as exc:
            print(f"{i:>3}. ERROR {row['email']}: {exc} — stopping batch")
            break
        time.sleep(SEND_DELAY_S)

    sender.close()
    if not DRY_RUN and sent_count:
        _audit(f"de outreach batch (Track B): {sent_count} emails, "
               f"mode={sender.mode}")
    print("\nbatch done")


if __name__ == "__main__":
    main()
