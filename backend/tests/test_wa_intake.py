"""WhatsApp 24/7 receptionist (D-054 F4 / D-055): intake state machine,
phone-prefix localization and country scoping.

Uses an in-memory Redis stand-in and stubs the LLM classifier and the
DB-writing finish step — the tests cover the conversational flow itself.
"""
import pytest

from app.i18n import tr
from app.jurisdictions import country_for_phone
from app.services import wa_intake


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.store:
            return None
        self.store[key] = value
        return True

    async def delete(self, key):
        self.store.pop(key, None)

    async def aclose(self):
        pass


@pytest.fixture
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(wa_intake.aioredis, "from_url", lambda url: r)
    return r


@pytest.fixture
def stub_llm_and_finish(monkeypatch):
    async def fake_classify(description):
        return {"category": "labor", "city": None, "urgency": "normal"}

    finished: list[dict] = []

    async def fake_finish(phone, state):
        finished.append(state)
        return "OK-POSTED"

    monkeypatch.setattr(wa_intake, "_classify", fake_classify)
    monkeypatch.setattr(wa_intake, "_finish_intake", fake_finish)
    return finished


def test_country_for_phone_prefixes():
    assert country_for_phone("38344123456") == "XK"
    assert country_for_phone("4915112345678") == "DE"
    assert country_for_phone("+49 151 1234") == "DE"
    assert country_for_phone("13475551234") == "XK"  # unknown → default
    assert country_for_phone(None) == "XK"


@pytest.mark.anyio
async def test_non_intake_message_returns_none(fake_redis):
    assert await wa_intake.handle_intake_message("383441", "Sa është afati i ankesës?") is None


@pytest.mark.anyio
async def test_full_flow_posts_case(fake_redis, stub_llm_and_finish):
    phone = "38344123"
    assert await wa_intake.handle_intake_message(phone, "RAST") == tr("sq", "wa_start")
    # too-short description is rejected, state stays on describe
    assert await wa_intake.handle_intake_message(phone, "u rrëzova") == tr("sq", "wa_too_short")
    reply = await wa_intake.handle_intake_message(
        phone, "Punëdhënësi nuk më ka paguar tri paga të fundit dhe më largoi nga puna pa vendim."
    )
    assert reply == tr("sq", "wa_ask_city")  # classifier found no city
    assert await wa_intake.handle_intake_message(phone, "Prishtinë") == tr("sq", "wa_ask_name")
    assert await wa_intake.handle_intake_message(phone, "Filan Fisteku") == tr("sq", "wa_ask_email")
    # invalid email re-asks
    assert await wa_intake.handle_intake_message(phone, "jo-email") == tr("sq", "wa_bad_email")
    assert await wa_intake.handle_intake_message(phone, "filan@example.com") == "OK-POSTED"

    state = stub_llm_and_finish[0]
    assert state["category"] == "labor"
    assert state["city"] == "Prishtinë"
    assert state["name"] == "Filan Fisteku"
    assert state["email"] == "filan@example.com"
    assert state["country"] == "XK" and state["locale"] == "sq"
    # state cleared — next message is normal Q&A again
    assert await wa_intake.handle_intake_message(phone, "faleminderit") is None


@pytest.mark.anyio
async def test_german_sender_gets_german_flow(fake_redis, stub_llm_and_finish):
    phone = "4915112345678"
    start = await wa_intake.handle_intake_message(phone, "FALL")
    assert start == tr("de", "wa_start")
    assert "KI-Assistentin" in start
    reply = await wa_intake.handle_intake_message(
        phone, "Mein Arbeitgeber hat mir fristlos gekündigt, ohne Abmahnung, letzte Woche in Berlin."
    )
    assert reply == tr("de", "wa_ask_city")
    await wa_intake.handle_intake_message(phone, "Berlin")
    await wa_intake.handle_intake_message(phone, "Max Mustermann")
    assert await wa_intake.handle_intake_message(phone, "max@example.de") == "OK-POSTED"

    state = stub_llm_and_finish[0]
    assert state["country"] == "DE" and state["locale"] == "de"


@pytest.mark.anyio
async def test_classifier_city_skips_city_question(fake_redis, monkeypatch, stub_llm_and_finish):
    async def classify_with_city(description):
        return {"category": "family", "city": "Gjakovë", "urgency": "urgent"}

    monkeypatch.setattr(wa_intake, "_classify", classify_with_city)
    phone = "38345999"
    await wa_intake.handle_intake_message(phone, "fall")
    reply = await wa_intake.handle_intake_message(
        phone, "Bashkëshorti nuk e respekton vendimin e gjykatës për kontaktin me fëmijët tanë."
    )
    assert reply == tr("sq", "wa_ask_name")


@pytest.mark.anyio
async def test_cancel_aborts_flow(fake_redis):
    phone = "38346111"
    await wa_intake.handle_intake_message(phone, "RAST")
    assert await wa_intake.handle_intake_message(phone, "ANULO") == tr("sq", "wa_cancelled")
    assert await wa_intake.handle_intake_message(phone, "përshëndetje") is None


@pytest.mark.anyio
async def test_cancel_without_flow_is_normal_message(fake_redis):
    assert await wa_intake.handle_intake_message("38347", "stop") is None


@pytest.mark.anyio
async def test_daily_hint_once_per_day_and_localized(fake_redis):
    first = await wa_intake.daily_hint("redis://x", "38348", "sq")
    second = await wa_intake.daily_hint("redis://x", "38348", "sq")
    assert first == tr("sq", "wa_hint") and "RAST" in first
    assert second == ""
    de = await wa_intake.daily_hint("redis://x", "4915199", "de")
    assert de == tr("de", "wa_hint") and "FALL" in de
