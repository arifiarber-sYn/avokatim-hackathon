"""Tests for the German outreach automation (harvester ranking, campaign
letter, and the shared opt-out classifier in the inbox triage)."""
import importlib

import pytest

triage = importlib.import_module("scripts.ops_inbox_triage")
campaign = importlib.import_module("scripts.de_outreach_campaign")
harvest = importlib.import_module("scripts.scrape_de_lawyers")


@pytest.mark.parametrize("subject,body,expected", [
    ("Herr", "STOP", "optout"),
    ("Re: Ava Legal", "Bitte abmelden, keine Werbung mehr.", "optout"),
    ("unsubscribe", "", "optout"),
    ("Re", "Mos me shkruani me, ju lutem.", "optout"),
    # A long human reply that merely contains the word "stop" must NOT be
    # suppressed — a false positive silently drops a hot lead forever.
    ("Interesse", "Wir nutzen Advoware, aber STOP ist kein Thema, "
                  "erzaehlen Sie mehr ueber die KI und die Preise fuer "
                  "meine Kanzlei mit fuenf Anwaelten bitte.", "human"),
    ("AW: Ihre Kanzlei", "Klingt spannend, koennen wir telefonieren? "
                         "Ich haette Fragen zur Migration aus RA-MICRO.", "human"),
])
def test_optout_classifier(subject, body, expected):
    # 2026-09-07 (incidenti Solar72): "human" kërkon lidhje mekanike me firmën
    # — kancelaria DE është në ledger-in e outreach-it tonë (ne i shkruam të
    # parët), prandaj firm_linked=True. Optout-i fiton pavarësisht lidhjes.
    assert triage._classify("kanzlei@example.de", subject, body,
                            firm_linked=True) == expected


def test_optout_ledger_dedup(tmp_path, monkeypatch):
    ledger = tmp_path / "de_suppress.txt"
    monkeypatch.setattr(triage, "SUPPRESS_LEDGER", ledger)
    assert triage._record_optout("Kanzlei@Example.DE") is True
    assert triage._record_optout("kanzlei@example.de") is False  # case-insensitive
    assert triage._record_optout("not-an-email") is False
    lines = [l for l in ledger.read_text().splitlines() if not l.startswith("#")]
    assert lines == ["kanzlei@example.de"]


def test_campaign_salutation_and_brand():
    frau = campaign.salutation({"anrede": "Frau", "titel": "Dr.", "nachname": "Krasniqi"})
    herr = campaign.salutation({"anrede": "Herr", "titel": "", "nachname": "Meyer"})
    anon = campaign.salutation({"anrede": "", "nachname": ""})
    assert frau == "Sehr geehrte Frau Dr. Krasniqi,"
    assert herr == "Sehr geehrter Herr Meyer,"
    assert anon == "Sehr geehrte Damen und Herren,"


def test_campaign_letter_is_ava_legal_only():
    body = campaign.BODY.format(
        anrede_line=campaign.salutation({"anrede": "Herr", "titel": "", "nachname": "Meyer"}),
        area_line=campaign.area_line({"rechtsgebiete": "Familienrecht; Erbrecht"}),
    )
    # Ava Legal brand + DE domain only; never AvokatIM / Kosovo to a prospect.
    assert "Ava Legal" in body
    assert "de.avokatiim.ai" in body
    assert "AvokatIM" not in body
    assert "Kosov" not in body
    assert "39" in body  # the Gründungspartner price anchor


def test_harvester_albanian_score_ranks_diaspora_first():
    assert harvest.albanian_score("Arta", "Krasniqi") >= 2
    assert harvest.albanian_score("Liridon", "Berisha") >= 2
    assert harvest.albanian_score("Thomas", "Müller") == 0


def test_pending_rows_in_batch_dedup():
    """O4 (audit 2026-08-20): a duplicate row inside one harvested batch must
    not double-send — the XK 'Vuksani' incident, now covered on DE too."""
    rows = [
        {"email": "a@example.de", "nachname": "Eins"},
        {"email": "A@Example.DE", "nachname": "Eins-Dublikat"},  # in-batch dup
        {"email": "b@example.de", "nachname": "Zwei"},
        {"email": "c@example.de", "nachname": "Gesendet"},
        {"email": "d@example.de", "nachname": "Unterdrueckt"},
        {"email": "", "nachname": "OhneAdresse"},
    ]
    out = campaign.pending_rows(rows, sent={"c@example.de"},
                                suppress={"d@example.de"})
    assert [r["email"].lower() for r in out] == ["a@example.de", "b@example.de"]
    assert out[0]["nachname"] == "Eins"  # the first occurrence wins
