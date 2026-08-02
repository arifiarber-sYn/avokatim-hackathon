"""WhatsApp 24/7 receptionist (D-054 F4): intake state machine.

Uses an in-memory Redis stand-in and stubs the LLM classifier and the
DB-writing finish step — the tests cover the conversational flow itself.
"""
import pytest

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


@pytest.mark.anyio
async def test_non_intake_message_returns_none(fake_redis):
    assert await wa_intake.handle_intake_message("383441", "Sa është afati i ankesës?") is None


@pytest.mark.anyio
async def test_full_flow_posts_case(fake_redis, stub_llm_and_finish):
    phone = "38344123"
    assert await wa_intake.handle_intake_message(phone, "RAST") == wa_intake.MSG["start"]
    # too-short description is rejected, state stays on describe
    assert await wa_intake.handle_intake_message(phone, "u rrëzova") == wa_intake.MSG["too_short"]
    reply = await wa_intake.handle_intake_message(
        phone, "Punëdhënësi nuk më ka paguar tri paga të fundit dhe më largoi nga puna pa vendim."
    )
    assert reply == wa_intake.MSG["ask_city"]  # classifier found no city
    assert await wa_intake.handle_intake_message(phone, "Prishtinë") == wa_intake.MSG["ask_name"]
    assert await wa_intake.handle_intake_message(phone, "Filan Fisteku") == wa_intake.MSG["ask_email"]
    # invalid email re-asks
    assert await wa_intake.handle_intake_message(phone, "jo-email") == wa_intake.MSG["bad_email"]
    assert await wa_intake.handle_intake_message(phone, "filan@example.com") == "OK-POSTED"

    state = stub_llm_and_finish[0]
    assert state["category"] == "labor"
    assert state["city"] == "Prishtinë"
    assert state["name"] == "Filan Fisteku"
    assert state["email"] == "filan@example.com"
    # state cleared — next message is normal Q&A again
    assert await wa_intake.handle_intake_message(phone, "faleminderit") is None


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
    assert reply == wa_intake.MSG["ask_name"]


@pytest.mark.anyio
async def test_cancel_aborts_flow(fake_redis):
    phone = "38346111"
    await wa_intake.handle_intake_message(phone, "RAST")
    assert await wa_intake.handle_intake_message(phone, "ANULO") == wa_intake.MSG["cancelled"]
    assert await wa_intake.handle_intake_message(phone, "përshëndetje") is None


@pytest.mark.anyio
async def test_cancel_without_flow_is_normal_message(fake_redis):
    assert await wa_intake.handle_intake_message("38347", "stop") is None


@pytest.mark.anyio
async def test_daily_hint_once_per_day(fake_redis):
    first = await wa_intake.daily_hint("redis://x", "38348")
    second = await wa_intake.daily_hint("redis://x", "38348")
    assert first == wa_intake.MSG["hint"]
    assert second == ""
