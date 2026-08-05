"""Tests for the Track A company outreach (D-062): the buyer-pipeline tool
with PO/JO gating, and the "company" class in the inbox triage."""
import csv
import importlib
from datetime import UTC, datetime, timedelta

import pytest

triage = importlib.import_module("scripts.ops_inbox_triage")
outreach = importlib.import_module("scripts.de_company_outreach")

DOMAINS = {"advocard.de": "ADVOCARD", "roland-rechtsschutz.de": "ROLAND"}


# --- triage: class "company" -------------------------------------------------

def test_company_class_beats_human_and_optout():
    # Normal reply from a target company
    assert triage._classify(
        "Max Muster <max.muster@advocard.de>", "AW: Angebot",
        "Gerne mehr Details.", DOMAINS,
    ) == "company"
    # Even a terse STOP from a target company is an M&A signal for the owner,
    # never a silent suppression.
    assert triage._classify(
        "legal@roland-rechtsschutz.de", "STOP", "", DOMAINS,
    ) == "company"
    # Non-target senders keep the old behavior
    assert triage._classify("someone@example.de", "Frage", "Hallo", DOMAINS) == "human"
    assert triage._classify("someone@example.de", "STOP", "", DOMAINS) == "optout"


def test_company_subdomain_matches_target_domain():
    match = triage._match_company("noreply@mail.advocard.de", DOMAINS)
    assert match == ("advocard.de", "ADVOCARD")
    assert triage._match_company("x@advocard.de.evil.com", DOMAINS) is None


def test_company_reply_ledger_dedup(tmp_path, monkeypatch):
    ledger = tmp_path / "de_company_replies.txt"
    monkeypatch.setattr(triage, "COMPANY_REPLIES", ledger)
    triage._record_company_reply("Advocard.DE")
    triage._record_company_reply("advocard.de")
    lines = [l for l in ledger.read_text().splitlines() if not l.startswith("#")]
    assert lines == ["advocard.de"]


# --- outreach tool: letters --------------------------------------------------

def _company(**over):
    base = {
        "wave": "1", "score": "15", "company": "ADVOCARD",
        "category": "insurer", "domain": "advocard.de",
        "contact_email": "nachricht@advocard.de", "letter_lang": "de",
        "offer_option": "1",
        "fit_reason": "shenim intern shqip qe s'del kurre ne leter",
        "fit_letter": "Ihr Geschäftsmodell verbindet Versicherte mit Anwälten.",
        "status": "new",
    }
    base.update(over)
    return base


def test_cover_letter_de_uses_target_language_fit():
    subject, body = outreach.cover_letter(_company())
    assert "Ava Legal" in body and "de.avokatiim.ai" in body
    assert "Ihr Geschäftsmodell" in body
    # The internal Albanian note must never leak into the letter.
    assert "shenim intern" not in body
    assert "AvokatIM" not in body and "Kosov" not in body
    assert "OEM-Lizenz" in body  # option 1 label, German


def test_cover_letter_en_for_english_targets():
    subject, body = outreach.cover_letter(_company(
        company="Septeo", letter_lang="en", offer_option="3",
        fit_letter="your growth model is acquisition.",
    ))
    assert "Dear Septeo team" in body
    assert "Full acquisition of the platform for DACH" in body
    assert "Kind regards" in body


# --- outreach tool: pipeline -------------------------------------------------

@pytest.fixture()
def pipeline(tmp_path, monkeypatch):
    companies = tmp_path / "de_companies.csv"
    fields = list(_company().keys())
    with companies.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerow(_company())
        w.writerow(_company(company="ROLAND", domain="roland-rechtsschutz.de",
                            score="14", contact_email="service@roland-rechtsschutz.de"))
        w.writerow(_company(company="JUPUS", domain="jupus.de", wave="3",
                            score="7", contact_email="", status="hold"))
    monkeypatch.setattr(outreach, "COMPANIES", companies)
    monkeypatch.setattr(outreach, "LOG", tmp_path / "log.csv")
    monkeypatch.setattr(outreach, "REPLIES", tmp_path / "replies.txt")
    monkeypatch.setattr(outreach, "build_offer_pdf",
                        lambda lang: tmp_path / f"offer-{lang}.pdf")
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(outreach, "_notify",
                        lambda kind, text, dry_run: sent.append((kind, text)))
    return sent


def test_propose_orders_by_wave_skips_hold_and_dedups(pipeline):
    outreach.propose(5, dry_run=False)
    kinds = [k for k, _ in pipeline]
    assert kinds == ["lead-m&a", "lead-m&a"]  # hold row never proposed
    assert "ADVOCARD" in pipeline[0][1]       # highest score first
    log = outreach.load_log()
    assert [r["status"] for r in log] == ["proposed", "proposed"]
    # A second run proposes nothing new
    outreach.propose(5, dry_run=False)
    assert len(pipeline) == 2


def test_followups_after_10_days_skip_replied(pipeline, monkeypatch):
    outreach.propose(5, dry_run=False)
    pipeline.clear()
    log = outreach.load_log()
    old = (datetime.now(UTC) - timedelta(days=11)).isoformat(timespec="seconds")
    for row in log:
        row["proposed_at"] = old
    outreach.save_log(log)
    # ROLAND already replied — must never get a nudge.
    outreach.REPLIES.write_text("roland-rechtsschutz.de\n", encoding="utf-8")

    outreach.followups(dry_run=False)
    assert len(pipeline) == 1
    assert "ADVOCARD" in pipeline[0][1]
    statuses = {r["company"]: r["status"] for r in outreach.load_log()}
    assert statuses == {"ADVOCARD": "followup", "ROLAND": "proposed"}
    # Follow-up happens once only
    pipeline.clear()
    outreach.followups(dry_run=False)
    assert pipeline == []
