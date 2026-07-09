"""Backend i18n catalog (Law 02/L-37 languages) and AML seed data checks."""
from app.i18n import CATALOG, _SQ, bilabel, normalize_locale, pick_locale, tr
from app.seeds.kosovo import XK_AML_INDICATORS, XK_AML_SCOPE_HINT

ALL_LOCALES = ["sq", "sr", "tr", "bs", "en", "zh"]


def test_normalize_locale():
    assert normalize_locale("sr") == "sr"
    assert normalize_locale("SR") == "sr"
    assert normalize_locale("sr-Latn-RS") == "sr"
    assert normalize_locale(None) == "sq"
    assert normalize_locale("fr") == "sq"


def test_pick_locale_chain():
    # contact locale wins, then tenant default, then Albanian
    assert pick_locale("tr", "en") == "tr"
    assert pick_locale(None, "en") == "en"
    assert pick_locale(None, None) == "sq"
    assert pick_locale("xx", "bs") == "bs"


def test_catalog_covers_all_official_languages():
    assert set(ALL_LOCALES) <= set(CATALOG.keys())
    # Every key defined in Albanian must exist in every other catalog
    for code in ALL_LOCALES:
        missing = set(_SQ.keys()) - set(CATALOG[code].keys())
        assert not missing, f"{code} is missing keys: {sorted(missing)}"


def test_tr_translates_and_falls_back():
    sq = tr("sq", "reminder_matter")
    sr = tr("sr", "reminder_matter")
    assert sq and sr and sq != sr
    # Placeholders are substituted
    subject = tr("tr", "reminder_subject", days=3, title="Ankesa")
    assert "3" in subject and "Ankesa" in subject
    # Unknown locale falls back to Albanian
    assert tr("fr", "reminder_matter") == sq


def test_bilabel_pairs_albanian_with_client_language():
    only_sq = bilabel("sq", "inv_subtotal")
    assert "/" not in only_sq
    both = bilabel("sr", "inv_subtotal")
    assert only_sq in both and "/" in both


def test_aml_indicators_have_all_languages():
    assert len(XK_AML_INDICATORS) >= 8
    for ind in XK_AML_INDICATORS:
        assert ind["code"].startswith("aml.")
        assert set(ALL_LOCALES) <= set(ind["text"].keys()), ind["code"]
    assert set(ALL_LOCALES) <= set(XK_AML_SCOPE_HINT.keys())
