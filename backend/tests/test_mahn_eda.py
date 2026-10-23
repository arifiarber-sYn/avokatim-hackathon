"""EDA export for the automatisiertes Mahnverfahren (D-059 F7, Beta):
record structure per the public spec — fixed 128-char records, uppercase
transliteration, amounts in cents, dates TTMMJJJJ — plus the Mahngericht
routing table and address splitting."""

from datetime import date
from decimal import Decimal

from app.services.mahn_eda import (
    LAYOUTS,
    MAHNGERICHTE,
    RECORD_LENGTH,
    build_mahn_eda,
    build_record,
    cents,
    eda_date,
    eda_text,
    split_de_address,
)


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _fixtures():
    tenant = _Obj(
        name="Kanzlei Müller & Partner",
        address="Bahnhofstraße 12, 50667 Köln",
        region="NW",
        country="DE",
    )
    contact = _Obj(
        display_name="Jörg Schäfer",
        address="Hauptstraße 5, 10115 Berlin",
        kind="person",
    )
    invoice = _Obj(
        number="RE-2026-042",
        issued_on=date(2026, 6, 1),
        due_on=date(2026, 7, 1),
        total_with_vat=Decimal("1547.35"),
    )
    return tenant, contact, invoice


def test_layout_widths_all_sum_to_record_length():
    for satzart, fields in LAYOUTS.items():
        assert sum(w for _, w in fields) == RECORD_LENGTH - 2, satzart


def test_every_bundesland_routes_to_a_mahngericht():
    assert set(MAHNGERICHTE) == {
        "BW", "BY", "BE", "BB", "HB", "HH", "MV", "HE",
        "NI", "NW", "RP", "SL", "SN", "ST", "TH", "SH",
    }


def test_eda_text_uppercases_and_transliterates():
    assert eda_text("Müller-Straße 12ß", 20) == "MUELLER-STRASSE 12SS"
    assert len(eda_text("x", 10)) == 10


def test_eda_date_and_cents():
    assert eda_date(date(2026, 7, 1)) == "01072026"
    assert eda_date(None) == "00000000"
    assert cents(Decimal("1547.35")) == 154735
    assert cents(0.1) == 10  # no float drift


def test_split_de_address():
    assert split_de_address("Bahnhofstraße 12, 50667 Köln") == (
        "Bahnhofstraße 12", "50667", "Köln"
    )
    street, plz, city = split_de_address("Kein PLZ hier")
    assert (plz, city) == ("", "")


def test_build_record_length_and_unknown_field():
    rec = build_record("01", {"name": "Test", "plz": "50667"})
    assert len(rec) == RECORD_LENGTH
    assert rec.startswith("01")
    try:
        build_record("01", {"bogus": "x"})
        raise AssertionError("unknown field must raise")
    except ValueError:
        pass


def test_full_eda_structure():
    tenant, contact, invoice = _fixtures()
    eda = build_mahn_eda(invoice=invoice, tenant=tenant, contact=contact)

    assert [r[:2] for r in eda.records] == ["VS", "01", "04", "05", "07", "NS"]
    assert all(len(r) == RECORD_LENGTH for r in eda.records)
    assert eda.total_cents == 154735
    assert eda.court["city"] == "Hagen"  # NW routes to AG Hagen
    assert eda.warnings == []

    text = eda.as_text()
    assert "KANZLEI MUELLER & PARTNER" in text
    assert "JOERG SCHAEFER" in text
    assert "000000154735" in text  # amount in zero-padded cents
    assert "01072026" in text  # interest runs from the due date
    # file is transliterated — no umlauts survive
    assert not any(ch in text for ch in "äöüÄÖÜß")
    # CRLF line endings, one per record
    assert text.count("\r\n") == len(eda.records)


def test_missing_region_and_plz_produce_warnings():
    tenant, contact, invoice = _fixtures()
    tenant.region = None
    contact.address = "irgendwo"
    eda = build_mahn_eda(invoice=invoice, tenant=tenant, contact=contact)
    assert len(eda.warnings) == 2
    assert [r[:2] for r in eda.records] == ["VS", "01", "04", "05", "07", "NS"]
