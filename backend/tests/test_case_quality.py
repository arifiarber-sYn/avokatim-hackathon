"""Heuristic layer of the marketplace case-quality gate."""
from app.services.case_quality import heuristic_check


def test_rejects_repetitive_spam():
    ok, reason = heuristic_check("mkan rre,mkan rre,mkan rre,mkan rre,mkan rre,mkan rre,mkan rre")
    assert ok is False
    assert reason == "repetitive"


def test_rejects_too_short():
    ok, reason = heuristic_check("haj kuku")
    assert ok is False
    assert reason == "too_few_words"


def test_rejects_gibberish_without_vowels():
    ok, reason = heuristic_check("xkcd qwrtp zzzz bcdfg hjklm")
    assert ok is False
    assert reason == "gibberish"


def test_accepts_real_case():
    ok, reason = heuristic_check(
        "Kam pasur një aksident trafiku në Prishtinë javën e kaluar dhe "
        "sigurimi po refuzon të paguajë dëmin. Çfarë hapash duhet të ndjek?"
    )
    assert ok is True
    assert reason == "ok"


def test_accepts_short_but_clear():
    ok, _ = heuristic_check("Ndihmë rreth aksidentit në trafik me lëndime")
    assert ok is True
