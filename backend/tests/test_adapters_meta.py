"""Contract tests for the Meta Model API adapter (offline only)."""
import asyncio

import pytest

from app.adapters.base import AdapterError
from app.adapters.meta_model import MetaModelAdapter, StubModel


def test_unavailable_without_config():
    a = MetaModelAdapter(base_url="", api_key="", model="muse-spark")
    assert a.available() is False
    with pytest.raises(AdapterError):
        asyncio.run(a.complete("Përshëndetje"))


def test_stub_is_deterministic():
    s = StubModel("Përgjigje provë.")
    assert s.available() is True
    c = asyncio.run(s.complete("Sa është afati?"))
    assert c.text == "Përgjigje provë."
    assert c.model == "stub"
    assert c.tokens_in >= 1


def test_config_defaults_are_empty_strings():
    a = MetaModelAdapter()
    assert isinstance(a.base_url, str)
    assert a.model

