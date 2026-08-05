"""Ava Legal — Track A outreach to German legal-tech / legal companies that
could buy or license the platform (NOT the 39 EUR/month lawyer campaign).

This is high-value M&A correspondence, so NOTHING is ever sent automatically.
The tool prepares a personalized cover letter + the full offer as a PDF
attachment and hands it to Halim (OpenClaw) via `notify_ops`; Halim shows the
draft to the owner on Telegram and only sends after an explicit "PO", using
`ops_send_reply.py --attach <offer.pdf>`.

Pipeline source: data/de_companies.csv (built from docs/pitch/
hulumtimi-blersit-de.md — the buyer research dossier), ordered by wave/score.
State: data/de_company_outreach_log.csv. Inbound replies are surfaced by
ops_inbox_triage (class "company"), which records answered domains in
data/de_company_replies.txt so follow-ups skip them.

Usage:
    python scripts/de_company_outreach.py --list
    python scripts/de_company_outreach.py --propose 3            # next 3 (PO/JO)
    python scripts/de_company_outreach.py --propose 3 --dry-run  # print only
    python scripts/de_company_outreach.py --followups            # 10-day nudges
"""
import argparse
import asyncio
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import PROJECT_DIR  # noqa: E402

DATA = PROJECT_DIR / "data"
COMPANIES = DATA / "de_companies.csv"
LOG = DATA / "de_company_outreach_log.csv"
REPLIES = DATA / "de_company_replies.txt"
PDF_DIR = DATA / "outreach_pdfs"
OFFER_DE = PROJECT_DIR / "docs" / "pitch" / "ava-legal-platform-offer-de.txt"
OFFER_EN = PROJECT_DIR / "docs" / "pitch" / "ava-legal-platform-offer.txt"

FOLLOWUP_AFTER_DAYS = 10

OFFER_LABELS = {
    "de": {
        "1": "OEM-Lizenz der KI-Schicht",
        "2": "Exklusive White-Label-Lizenz für DACH",
        "3": "Vollständiger Erwerb der Plattform für DACH",
        "4": "Vollständiger globaler Erwerb",
    },
    "en": {
        "1": "OEM license of the AI layer",
        "2": "Exclusive white-label license for DACH",
        "3": "Full acquisition of the platform for DACH",
        "4": "Full global acquisition",
    },
}


def load_companies() -> list[dict]:
    with COMPANIES.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: (int(r["wave"]), -int(r["score"])))
    return rows


def load_log() -> list[dict]:
    if not LOG.exists():
        return []
    with LOG.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_log(rows: list[dict]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "company", "domain", "contact_email", "wave", "status",
            "proposed_at", "followup_at", "offer_option", "pdf_path",
        ])
        w.writeheader()
        w.writerows(rows)


def replied_domains() -> set[str]:
    if not REPLIES.exists():
        return set()
    return {l.strip().lower() for l in REPLIES.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")}


def build_offer_pdf(lang: str) -> Path:
    """Render the offer .txt to a clean A4 PDF (once per language)."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / f"ava-legal-offer-{lang}.pdf"
    if out.exists():
        return out
    import html as html_mod

    from weasyprint import HTML

    src = OFFER_DE if lang == "de" else OFFER_EN
    text = html_mod.escape(src.read_text(encoding="utf-8"))
    page = (
        "<html><head><meta charset='utf-8'><style>"
        "@page { size: A4; margin: 20mm; }"
        "body { font-family: 'DejaVu Sans', Arial, sans-serif; }"
        "pre { white-space: pre-wrap; font-family: inherit; font-size: 10.5px;"
        " line-height: 1.4; }"
        "</style></head><body><pre>" + text + "</pre></body></html>"
    )
    HTML(string=page).write_pdf(str(out))
    return out


def cover_letter(company: dict) -> tuple[str, str]:
    """Return (subject, body) in the company's target language, citing the
    specific fit reason and opening with the chosen offer option."""
    lang = company.get("letter_lang", "de")
    opt = OFFER_LABELS.get(lang, OFFER_LABELS["de"]).get(company["offer_option"], "")
    name = company["company"]
    # fit_letter is written in the target language; fit_reason stays an
    # internal (Albanian) note and must never appear in the letter.
    fit = company.get("fit_letter") or company["fit_reason"]
    if lang == "en":
        subject = "AI-native legal platform — license or acquisition (Ava Legal)"
        body = (
            f"Dear {name} team,\n\n"
            "we have built a complete, AI-native legal practice platform for "
            "the German market — RVG billing, ZPO/ArbGG/VwGO deadlines, "
            "e-invoicing (ZUGFeRD/XRechnung, DATEV), Mahnwesen with EDA export, "
            "plus a corpus-grounded AI assistant (German law + 16,000+ court "
            "decisions, automatic citation verification) and 24/7 client "
            "intake by web, WhatsApp and phone. Live in production today.\n\n"
            f"Why we are writing specifically to you: {fit}\n\n"
            f"We would open the conversation around: {opt}. The attached "
            "document is our complete offer with four options and final "
            "prices. Our strength is engineering speed, not distribution in "
            "Germany — yours is exactly that.\n\n"
            "A live demonstration on the production system is possible within "
            "a week, on-site or remote. The offer went to a small number of "
            "selected companies at the same time.\n\n"
            "Kind regards,\nArbër Arifi\nFounder · Ava Legal · "
            "https://de.avokatiim.ai"
        )
    else:
        subject = "KI-native Kanzleiplattform — Lizenz oder Erwerb (Ava Legal)"
        body = (
            f"Sehr geehrtes Team von {name},\n\n"
            "wir haben eine vollständige, KI-native Kanzleiplattform für den "
            "deutschen Markt gebaut — RVG-Abrechnung, Fristen nach ZPO/ArbGG/"
            "VwGO, E-Rechnung (ZUGFeRD/XRechnung, DATEV), Mahnwesen mit "
            "EDA-Export, dazu einen im Korpus verankerten KI-Assistenten "
            "(deutsches Recht + über 16.000 Entscheidungen, automatische "
            "Zitatverifizierung) und eine 24/7-Mandantenaufnahme per Web, "
            "WhatsApp und Telefon. Heute live im Produktivbetrieb.\n\n"
            f"Warum wir gerade Sie ansprechen: {fit}\n\n"
            f"Wir würden das Gespräch mit folgender Option eröffnen: {opt}. "
            "Das beigefügte Dokument ist unser vollständiges Angebot mit vier "
            "Optionen und finalen Preisen. Unsere Stärke ist "
            "Entwicklungsgeschwindigkeit, nicht der Vertrieb in Deutschland — "
            "Ihre ist genau das.\n\n"
            "Eine Live-Demonstration auf dem Produktivsystem ist innerhalb "
            "einer Woche möglich, vor Ort oder remote. Das Angebot ging "
            "zeitgleich an eine kleine Zahl ausgewählter Unternehmen.\n\n"
            "Mit freundlichen Grüßen\nArbër Arifi\nGründer · Ava Legal · "
            "https://de.avokatiim.ai"
        )
    return subject, body


def followup_letter(company: dict) -> tuple[str, str]:
    lang = company.get("letter_lang", "de")
    name = company["company"]
    if lang == "en":
        return (
            "Re: AI-native legal platform (Ava Legal)",
            f"Dear {name} team,\n\na brief follow-up on our offer from a couple "
            "of weeks ago. If a short live demonstration would be useful, I am "
            "happy to arrange one this week. If it is not a fit right now, a "
            "one-line reply is enough and I will not follow up again.\n\n"
            "Kind regards,\nArbër Arifi\nFounder · Ava Legal · "
            "https://de.avokatiim.ai",
        )
    return (
        "Re: KI-native Kanzleiplattform (Ava Legal)",
        f"Sehr geehrtes Team von {name},\n\nnur eine kurze Nachfrage zu unserem "
        "Angebot von vor zwei Wochen. Falls eine kurze Live-Demonstration "
        "hilfreich wäre, richte ich diese gern noch diese Woche ein. Passt es "
        "aktuell nicht, genügt eine kurze Antwort und ich melde mich nicht "
        "erneut.\n\nMit freundlichen Grüßen\nArbër Arifi\nGründer · Ava Legal "
        "· https://de.avokatiim.ai",
    )


def _ops_command(to: str, subject: str, pdf: Path) -> str:
    return (
        f"cd ~/AvokatIM/backend && echo \"TRUPI\" | .venv/bin/python "
        f"scripts/ops_send_reply.py --to \"{to}\" --subject \"{subject}\" "
        f"--attach \"{pdf}\""
    )


def _notify(kind: str, text: str, dry_run: bool) -> None:
    if dry_run:
        print("\n" + "=" * 70 + f"\n[{kind}]\n{text}\n")
        return
    from app.services.ops_notify import notify_ops
    asyncio.run(notify_ops(kind, text))


def propose(n: int, dry_run: bool) -> None:
    log = load_log()
    done_domains = {r["domain"].lower() for r in log}
    pool = [c for c in load_companies()
            if c["status"] != "hold" and c["domain"].lower() not in done_domains]
    batch = pool[:n]
    if not batch:
        print("no more companies to propose (all in the log or on hold)")
        return

    now = datetime.now(UTC).isoformat(timespec="seconds")
    for c in batch:
        pdf = build_offer_pdf(c.get("letter_lang", "de"))
        subject, body = cover_letter(c)
        to = c["contact_email"] or "(VERIFIKO adresën nga Impressum/LinkedIn)"
        text = (
            f"LEAD M&A (Kanali A) — propozim outreach për {c['company']}\n"
            f"Kategoria: {c['category']} · vala {c['wave']} · pikët {c['score']}\n"
            f"Marrësi: {to}\n"
            f"Oferta hapëse: Opsioni {c['offer_option']}\n"
            f"Bashkëngjitje: {pdf}\n\n"
            f"SUBJECT: {subject}\n\nDRAFT:\n{body}\n\n"
            "VEPRIMI: trego draftin te Kllosha, prit PO/JO. Nëse adresa mungon, "
            "gjeje të saktën nga Impressum/LinkedIn PARA dërgimit. Në 'PO' "
            "dërgo (zëvendëso TRUPI me draftin e mësipërm):\n"
            f"{_ops_command(c['contact_email'] or 'ADRESA', subject, pdf)}\n"
            "KURRË mos përmend çmimet-dysheme interne, kurrë Kosovën/AvokatIM."
        )
        _notify("lead-m&a", text, dry_run)
        log.append({
            "company": c["company"], "domain": c["domain"],
            "contact_email": c["contact_email"], "wave": c["wave"],
            "status": "proposed", "proposed_at": now, "followup_at": "",
            "offer_option": c["offer_option"], "pdf_path": str(pdf),
        })
        print(f"proposed: {c['company']} ({c['domain']}) → Halim")

    if not dry_run:
        save_log(log)


def followups(dry_run: bool) -> None:
    log = load_log()
    if not log:
        print("nothing proposed yet")
        return
    replied = replied_domains()
    companies = {c["domain"].lower(): c for c in load_companies()}
    now = datetime.now(UTC)
    changed = False
    for row in log:
        if row["status"] != "proposed":
            continue
        if row["domain"].lower() in replied:
            continue
        try:
            proposed = datetime.fromisoformat(row["proposed_at"])
        except ValueError:
            continue
        if (now - proposed).days < FOLLOWUP_AFTER_DAYS:
            continue
        company = companies.get(row["domain"].lower(), row)
        subject, body = followup_letter(company)
        to = row["contact_email"] or "(VERIFIKO adresën)"
        text = (
            f"FOLLOW-UP (Kanali A) — {row['company']} ({row['proposed_at'][:10]}, "
            f"pa përgjigje >{FOLLOWUP_AFTER_DAYS} ditë)\n"
            f"Marrësi: {to}\n\nSUBJECT: {subject}\n\nDRAFT:\n{body}\n\n"
            "VEPRIMI: trego te Kllosha, prit PO/JO. Kjo është nxitja e vetme."
        )
        _notify("lead-followup", text, dry_run)
        print(f"follow-up: {row['company']} → Halim")
        if not dry_run:
            row["status"] = "followup"
            row["followup_at"] = now.isoformat(timespec="seconds")
            changed = True
    if changed:
        save_log(log)
    elif not dry_run:
        print("no companies are due for a follow-up")


def show_list() -> None:
    log = {r["domain"].lower(): r for r in load_log()}
    replied = replied_domains()
    print(f"{'W':<2} {'score':<5} {'company':<34} {'status':<10} contact")
    for c in load_companies():
        r = log.get(c["domain"].lower())
        status = r["status"] if r else "—"
        if c["domain"].lower() in replied:
            status = "REPLIED"
        print(f"{c['wave']:<2} {c['score']:<5} {c['company'][:33]:<34} "
              f"{status:<10} {c['contact_email'] or '(verify)'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--propose", type=int, metavar="N")
    ap.add_argument("--followups", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.list:
        show_list()
    elif args.followups:
        followups(args.dry_run)
    elif args.propose:
        propose(args.propose, args.dry_run)
    else:
        show_list()


if __name__ == "__main__":
    main()
