"""Notary seed data: fee brackets per AI 02/2012 and act/checklist integrity.
The public /noteret calculator relies on these numbers being exact."""
from app.seeds.citizen_docs import CITIZEN_DOC_TEMPLATES
from app.seeds.notary import (
    NOTARY_ACTS,
    NOTARY_CHECKLIST_LABELS,
    annex1_fee,
)

ALL_LOCALES = ["sq", "sr", "tr", "bs", "en", "zh"]


def test_annex1_brackets():
    assert annex1_fee(100) == 20
    assert annex1_fee(2_500) == 20
    assert annex1_fee(2_501) == 30
    assert annex1_fee(5_001) == 50
    assert annex1_fee(20_001) == 80
    assert annex1_fee(60_001) == 120
    assert annex1_fee(100_000) == 120


def test_annex1_above_100k_steps_and_cap():
    # art. 21.2: +20 € per started 20 000 € above 100 000 €, capped at 1 000 €
    assert annex1_fee(100_001) == 140
    assert annex1_fee(120_000) == 140
    assert annex1_fee(120_001) == 160
    assert annex1_fee(5_000_000) == 1_000


def test_acts_localized_and_checklists_resolvable():
    for act in NOTARY_ACTS:
        for locale in ALL_LOCALES:
            assert act["name"][locale], (act["code"], locale)
        for key in act["checklist"]:
            label = NOTARY_CHECKLIST_LABELS[key]
            for locale in ALL_LOCALES:
                assert label[locale], (key, locale)
        assert act["act_type"] in {"akt", "solemnizim", "vertetim"}


def test_notary_pack_templates_link_to_real_acts():
    act_codes = {a["code"] for a in NOTARY_ACTS}
    notary_templates = [
        t for t in CITIZEN_DOC_TEMPLATES if t.get("requires_notary")
    ]
    assert len(notary_templates) == 4
    for tpl in notary_templates:
        assert tpl["category"] == "noteria"
        assert tpl["notary_act"] in act_codes, tpl["code"]
