from app.config import settings
from app.llm.base import LLMProvider
from app.llm.deepseek import DeepSeekProvider
from app.llm.local import LocalProvider

_PROVIDERS: dict[str, LLMProvider] = {
    "deepseek": DeepSeekProvider(),
    "local": LocalProvider(),
}


def get_provider(name: str | None = None) -> LLMProvider:
    provider = _PROVIDERS.get(name or settings.llm_provider)
    if provider is None:
        raise ValueError(f"Unknown LLM provider: {name}")
    if not provider.is_configured():
        raise RuntimeError(
            f"LLM provider '{provider.name}' is not configured "
            "(check backend/.env)"
        )
    return provider


def list_providers() -> list[dict]:
    return [
        {"name": p.name, "configured": p.is_configured()}
        for p in _PROVIDERS.values()
    ]
