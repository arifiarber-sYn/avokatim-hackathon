"""Push platform events to the OpenClaw operator assistant (Halim).

The gateway runs on this machine (loopback, token-protected). Each event is
POSTed to /hooks/agent, where the assistant formats it and forwards it to the
operator on Telegram (night rules etc. live in the assistant's
AVOKATIM-OPS.md, not here).

Strictly fire-and-forget: disabled without a token, never raises into user
flows, 5s timeout. This complements (does not replace) the operator emails.
"""
import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_INSTRUCTION = (
    "Ti je Halim. Lexo ~/.openclaw/workspace/AVOKATIM-OPS.md (seksioni "
    "'Ngjarjet e platformës') dhe vepro sipas tij: përcillja Kllosha-s në "
    "Telegram shqip, shkurt e qartë, me linkun përkatës. Respekto rregullin "
    "e natës — vetëm SOS dhe urgjencat mes 23:00–08:00; tjetrat mblidhen "
    "për raportin e mëngjesit."
)


def ops_notify_enabled() -> bool:
    return bool(settings.openclaw_hook_token and settings.openclaw_hook_url)


async def notify_ops(kind: str, text: str, urgent: bool = False) -> bool:
    """Send one event to the assistant. kind is a short slug shown in the
    event header (e.g. "sos", "verifikim", "regjistrim")."""
    if not ops_notify_enabled():
        return False
    payload = {
        "message": (
            f"[Ngjarje AvokatIM] lloji={kind} urgjente={'PO' if urgent else 'jo'}\n"
            f"{text}\n\n{_INSTRUCTION}"
        ),
        "name": "AvokatIM",
        "wakeMode": "now",
    }
    headers = {"Authorization": f"Bearer {settings.openclaw_hook_token}"}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(settings.openclaw_hook_url, json=payload, headers=headers)
            r.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("ops_notify (%s) failed: %s", kind, exc)
        return False


def notify_ops_bg(kind: str, text: str, urgent: bool = False) -> None:
    """Schedule the notification without awaiting it (for sync-ish paths where
    adding a FastAPI background task is inconvenient)."""
    try:
        asyncio.get_running_loop().create_task(notify_ops(kind, text, urgent))
    except RuntimeError:
        # No running loop (scripts/tests) — skip silently
        pass
