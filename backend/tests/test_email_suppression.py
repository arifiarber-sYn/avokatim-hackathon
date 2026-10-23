"""The central email sender must never mail simulation/test addresses:
they bounce back to the owner's Gmail inbox and damage sender reputation."""
from app.services.notifications import _is_test_recipient


def test_simulation_addresses_are_suppressed():
    assert _is_test_recipient("driton.sim.928866@gmail.com")
    assert _is_test_recipient("qytetari.sim.123456@gmail.com")
    assert _is_test_recipient("BLERTA.SIM.42@GMAIL.COM")
    # Suffixes are uuid hex — letters must match too (the bug that leaked
    # 22 bounces into the owner's inbox on 2026-07-13)
    assert _is_test_recipient("noteri.sim.f16bc8@gmail.com")
    assert _is_test_recipient("qytetari.sim.c9fcc8@gmail.com")
    assert _is_test_recipient("kontakt.ferro.c9fcc8@gmail.com")
    assert _is_test_recipient("skrap.b19b9c@gmail.com")
    # isolation_check.py probes (IsoTest A/B) — must never email or ping Halim
    assert _is_test_recipient("iso.a.d0a55d68@gmail.com")
    assert _is_test_recipient("iso.b.d0a55d68@gmail.com")


def test_reserved_and_seed_domains_are_suppressed():
    assert _is_test_recipient("anyone@example.com")
    assert _is_test_recipient("demo@avokatim.app")
    assert _is_test_recipient("x@avokatim.local")


def test_obvious_domain_typo_is_suppressed():
    assert _is_test_recipient("daaaaa@gmail.con")


def test_real_addresses_still_pass():
    assert not _is_test_recipient("marigonagashi.law@gmail.com")
    assert not _is_test_recipient("arifi.arber@gmail.com")
    assert not _is_test_recipient("someone@yopmail.com")
    assert not _is_test_recipient("simona@gmail.com")  # 'sim' inside a name is fine
    assert not _is_test_recipient("iso.krasniqi@gmail.com")  # real-looking 'iso' name
