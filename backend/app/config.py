"""Central configuration. Everything is overridable via environment / backend/.env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
PROJECT_DIR = BASE_DIR.parent                      # BoraLaw/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "BoraLaw"
    debug: bool = False

    # Database (docker-compose exposes Postgres on 127.0.0.1:5433)
    database_url: str = (
        "postgresql+psycopg://boralaw:boralaw-dev-password@127.0.0.1:5433/boralaw"
    )
    redis_url: str = "redis://127.0.0.1:6380/0"

    # Auth
    secret_key: str = "change-me-in-backend-.env"
    access_token_minutes: int = 60 * 12
    totp_issuer: str = "BoraLaw"

    # Document storage (encrypted at rest with Fernet derived from doc_encryption_key)
    documents_dir: Path = PROJECT_DIR / "data" / "documents"
    doc_encryption_key: str = ""  # empty = store unencrypted (dev only)

    # LLM providers. Provider is selectable per-request; this is the default.
    llm_provider: str = "deepseek"  # "deepseek" | "local"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-pro"
    deepseek_thinking_enabled: bool = True
    deepseek_max_tokens: int = 8000
    # Local OpenAI-compatible endpoint (Ollama / vLLM), phase 2 option
    local_llm_base_url: str = "http://127.0.0.1:11434/v1"
    local_llm_model: str = ""
    local_llm_api_key: str = "not-needed"

    # RAG / embeddings
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    # OCR
    ocr_languages: str = "sqi+eng+chi_sim"

    default_locale: str = "sq"
    supported_locales: list[str] = ["sq", "en", "zh"]

    # Public base URL used in links (calendar feed, public intake form)
    public_base_url: str = "http://127.0.0.1:3000"

    # Email notifications (deadline reminders). Empty smtp_host = disabled.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "BoraLaw <noreply@boralaw.local>"
    smtp_starttls: bool = True
    reminder_check_minutes: int = 60

    # Email-to-matter ingestion (IMAP). Empty imap_host = disabled.
    # Each matter gets an alias imap_user-local-part+<token>@domain (plus
    # addressing); the poller files incoming mail into the matter.
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"
    imap_poll_minutes: int = 5

    # SMS (Twilio-compatible API). Empty account SID = disabled.
    # Used for hearing reminders sent to the matter's client.
    sms_account_sid: str = ""
    sms_auth_token: str = ""
    sms_from: str = ""
    sms_api_base: str = "https://api.twilio.com"

    # Card payments (Stripe Checkout). Empty secret key = disabled.
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Web Push (PWA notifications). Generated once; empty = push disabled.
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:noreply@boralaw.local"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
