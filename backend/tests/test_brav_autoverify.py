"""Branch tests for the German BRAV auto-verification (D-046).

The BRAV portal call and the shared approval tail are monkeypatched, so
these tests exercise only the decision logic: unique match -> approve,
namesakes -> operator queue, portal down / no match -> manual hint.
"""
from types import SimpleNamespace

import pytest

import app.services.license_verify as lv
from app.services.brav import BravEntry, BravResult


class FakeDB:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


def _user():
    return SimpleNamespace(full_name="Katharina Müller", email="km@example.de")


def _profile():
    return SimpleNamespace(verification_note=None)


def _entry(first="Katharina", last="Müller", profession="Rechtsanwältin"):
    return BravEntry(
        last_name=last, first_name=first, profession=profession,
        office="Kanzlei X", city="Koblenz",
    )


@pytest.fixture
def capture(monkeypatch):
    """Patch the network + side-effect seams and record what was called."""
    calls = {"approve": None, "ops": [], "search": None}

    async def fake_approve(db, user, profile, **kwargs):
        calls["approve"] = kwargs
        return True

    async def fake_notify(subject, body):
        calls["ops"].append((subject, body))

    def set_search(result):
        async def fake_search(last, first="", city="", timeout=15.0):
            calls["search"] = (last, first)
            return result

        monkeypatch.setattr("app.services.brav.search_brav", fake_search)

    monkeypatch.setattr(lv, "_approve_profile", fake_approve)
    monkeypatch.setattr("app.services.ops_notify.notify_ops", fake_notify)
    calls["set_search"] = set_search
    return calls


@pytest.mark.anyio
async def test_unique_match_auto_approves(capture):
    capture["set_search"](BravResult(total=1, entries=[_entry()]))
    ok = await lv._try_auto_verify_brav(FakeDB(), _user(), _profile())
    assert ok is True
    assert capture["approve"]["registry"] == "BRAV"
    assert capture["approve"]["matched_by"] == "brav_unique_name"
    assert "BRAV-Eintrag" in capture["approve"]["note"]
    assert capture["search"] == ("Müller", "Katharina")


@pytest.mark.anyio
async def test_umlaut_variant_still_matches(capture):
    capture["set_search"](BravResult(total=1, entries=[_entry()]))
    user = SimpleNamespace(full_name="Katharina Mueller", email="km@example.de")
    ok = await lv._try_auto_verify_brav(FakeDB(), user, _profile())
    assert ok is True


@pytest.mark.anyio
async def test_multiple_matches_queue_for_ops(capture):
    capture["set_search"](BravResult(total=2, entries=[_entry(), _entry()]))
    db, profile = FakeDB(), _profile()
    ok = await lv._try_auto_verify_brav(db, _user(), profile)
    assert ok is False
    assert capture["approve"] is None
    assert "kandidatët" in profile.verification_note
    assert db.commits == 1
    assert any("shumë përputhje" in body for _, body in capture["ops"])


@pytest.mark.anyio
async def test_truncated_result_never_auto_approves(capture):
    # 11 total but only one page parsed — unseen namesakes may exist.
    capture["set_search"](BravResult(total=11, entries=[_entry()]))
    ok = await lv._try_auto_verify_brav(FakeDB(), _user(), _profile())
    assert ok is False
    assert capture["approve"] is None


@pytest.mark.anyio
async def test_non_lawyer_professions_are_ignored(capture):
    capture["set_search"](
        BravResult(total=1, entries=[_entry(profession="Steuerberaterin")])
    )
    profile = _profile()
    ok = await lv._try_auto_verify_brav(FakeDB(), _user(), profile)
    assert ok is False
    assert "BRAV" in profile.verification_note  # manual search hint


@pytest.mark.anyio
async def test_portal_down_falls_back_to_manual_hint(capture):
    capture["set_search"](None)
    profile = _profile()
    ok = await lv._try_auto_verify_brav(FakeDB(), _user(), profile)
    assert ok is False
    assert profile.verification_note == lv.brav_search_hint("Katharina Müller")
    assert any("s'u arrit" in body for _, body in capture["ops"])


@pytest.mark.anyio
async def test_no_match_falls_back_to_manual_hint(capture):
    capture["set_search"](BravResult(total=0, entries=[]))
    profile = _profile()
    ok = await lv._try_auto_verify_brav(FakeDB(), _user(), profile)
    assert ok is False
    assert any("asnjë përputhje" in body for _, body in capture["ops"])
