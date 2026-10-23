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

def _instruction() -> str:
    # The hook run is an isolated session WITHOUT chat delivery context: a
    # plain final reply goes nowhere. The assistant must call its message
    # tool with the explicit Telegram target to actually reach the operator.
    to = settings.openclaw_hook_to
    send_hint = (
        f"DËRGIMI: përdor veglën 'message' me target eksplicit Telegram, "
        f"chat id {to} — përgjigja jote finale NUK dorëzohet vetvetiu."
        if to
        else "DËRGIMI: përdor veglën 'message' me targetin e Kllosha-s në "
             "Telegram (shih AVOKATIM-OPS.md)."
    )
    return (
        "Ti je Halim. Lexo ~/.openclaw/workspace/AVOKATIM-OPS.md (seksioni "
        "'Ngjarjet e platformës') dhe vepro sipas tij: përcillja Kllosha-s "
        "në Telegram shqip, shkurt e qartë, me linkun përkatës. "
        f"{send_hint} Respekto rregullin e natës — vetëm SOS dhe urgjencat "
        "mes 23:00–08:00; tjetrat shënoji te memory/ për raportin e mëngjesit."
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
            f"{text}\n\n{_instruction()}"
        ),
        "name": "AvokatIM",
        "wakeMode": "now",
        # Required since the gateway hosts multiple agents (400 without it).
        "agentId": settings.openclaw_hook_agent_id,
    }
    if settings.openclaw_hook_to:
        # Explicit delivery context: the runner can verify the assistant's
        # message-tool send against the intended target (no ambiguity errors).
        payload["channel"] = "telegram"
        payload["to"] = settings.openclaw_hook_to
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
