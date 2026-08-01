"""Central configuration. Everything is overridable via environment / backend/.env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
PROJECT_DIR = BASE_DIR.parent                      # AvokatIM/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "AvokatIM"
    debug: bool = False

    # Database (docker-compose exposes Postgres on 127.0.0.1:5433)
    # database_url is the OWNER role (avokatim) — used by Alembic migrations
    # and admin scripts. The app itself connects as the non-superuser role in
    # database_app_url so Row-Level Security applies (D-033); empty = fall
    # back to database_url (dev/tests).
    database_url: str = (
        "postgresql+psycopg://avokatim:avokatim-dev-password@127.0.0.1:5433/avokatim"
    )
    database_app_url: str = ""
    redis_url: str = "redis://127.0.0.1:6380/0"

    # Auth
    secret_key: str = "change-me-in-backend-.env"
    access_token_minutes: int = 60 * 12
    totp_issuer: str = "AvokatIM"

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

    # Official languages of Kosovo (Law 02/L-37): sq + sr state-wide,
    # tr + bs in several municipalities; en/zh are extras.
    default_locale: str = "sq"
    supported_locales: list[str] = ["sq", "sr", "tr", "bs", "en", "zh", "de"]

    # Public base URL used in links (calendar feed, public intake form)
    public_base_url: str = "http://127.0.0.1:3000"

    # Social login for citizen accounts (Google / Apple / Meta). A provider's
    # button appears only when its credentials are set. Redirect URIs to
    # register with each provider:
    #   {public_base_url}/api/public/oauth/{google|apple|meta}/callback
    oauth_google_client_id: str = ""
    oauth_google_client_secret: str = ""
    # Apple "Sign in with Apple": Services ID (client id), Team ID, Key ID and
    # the .p8 private key (PEM contents or a file path) — requires the paid
    # Apple Developer Program.
    oauth_apple_client_id: str = ""
    oauth_apple_team_id: str = ""
    oauth_apple_key_id: str = ""
    oauth_apple_private_key: str = ""
    # Meta (Facebook Login)
    oauth_meta_client_id: str = ""
    oauth_meta_client_secret: str = ""

    # Email notifications (deadline reminders). Empty smtp_host = disabled.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "AvokatIM <noreply@avokatim.local>"
    smtp_starttls: bool = True
    # Also drives onboarding nudges (sent ~1h after signup), so keep it short
    reminder_check_minutes: int = 10

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

    # Card payments. Provider is selected here; a provider counts as enabled
    # only when its credentials below are set. "stripe" needs a foreign-
    # registered entity (Stripe does not onboard Kosovo businesses);
    # "raiffeisen" is the local gateway (see docs/integrimet/raiffeisen-pagesat.md).
    payments_provider: str = "stripe"  # stripe | raiffeisen
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    raiffeisen_api_base: str = ""
    raiffeisen_merchant_id: str = ""
    raiffeisen_api_key: str = ""
    raiffeisen_callback_secret: str = ""

    # Platform subscription billing: operator's bank details printed in the
    # subscription-invoice emails (bank transfer is the default rail until a
    # card gateway that operates in Kosovo is contracted).
    platform_bank_details: str = ""

    # LiveKit (SOS video/audio calls). Empty api key = video disabled.
    # Keys must match LIVEKIT_KEYS given to the livekit container (root .env).
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    # Client-facing signaling URL. Empty = the frontend derives it:
    # ws://127.0.0.1:7880 on localhost, wss://<host>:7443 (Caddy) on LAN.
    livekit_url: str = ""

    # Voice (AI protection by phone): local STT/TTS — audio never leaves
    # this machine. Models are downloaded once into data/models/ (git-ignored).
    # Empty/missing model dirs = voice endpoints report enabled=false.
    voice_stt_model_dir: Path = PROJECT_DIR / "data" / "models" / "whisper-sq-ct2"
    # "auto" = try CUDA (float16), fall back to CPU (int8). The RTX 5090 cuts
    # a 5 s utterance from ~9.6 s to ~1.2 s (voice audit 2026-08-01).
    voice_stt_device: str = "auto"
    # Fallback Whisper model for non-Albanian speech (downloaded on demand
    # by faster-whisper into its cache); empty = Albanian model handles all.
    voice_stt_fallback_model: str = "large-v3-turbo"
    voice_tts_model: Path = (
        PROJECT_DIR / "data" / "models" / "piper-sq" / "sq_AL-edon-medium.onnx"
    )
    # Piper runs as a subprocess (CLI) — GPL-3 isolation + no blocking imports
    voice_piper_bin: Path = BASE_DIR / ".venv" / "bin" / "piper"
    voice_stt_threads: int = 8
    voice_max_audio_seconds: int = 120
    voice_max_tts_chars: int = 900

    # Web Push (PWA notifications). Generated once; empty = push disabled.
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:noreply@avokatim.local"

    # WhatsApp Business Cloud API (Ava over WhatsApp). Empty token = the
    # webhook accepts but does not reply (buildable/testable without a Meta
    # business account; see docs/integrimet/whatsapp.md).
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_verify_token: str = ""
    # Meta App Secret — when set, webhook POSTs must carry a valid
    # X-Hub-Signature-256 (HMAC-SHA256 of the raw body)
    whatsapp_app_secret: str = ""
    whatsapp_api_base: str = "https://graph.facebook.com/v21.0"
    whatsapp_daily_limit: int = 20

    # OpenClaw operator assistant (Halim): platform events are pushed to the
    # local gateway's /hooks/agent endpoint and forwarded to the operator on
    # Telegram. Empty token = disabled. Loopback only — never expose the hook.
    # Hook agent turns have no chat delivery context of their own, so the
    # operator's Telegram chat id must be given explicitly (openclaw_hook_to).
    openclaw_hook_url: str = "http://127.0.0.1:18789/hooks/agent"
    openclaw_hook_token: str = ""
    openclaw_hook_to: str = ""  # Telegram chat id of the operator


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
