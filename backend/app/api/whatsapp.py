"""Ava over WhatsApp (Meta Business Cloud API).

Built as a testable stub: the webhook handshake and message parsing work
without any Meta credentials; the actual reply is sent only when
`whatsapp_token` + `whatsapp_phone_id` are configured in backend/.env.
Setup steps for the owner are documented in docs/integrimet/whatsapp.md.
"""
import logging

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/public/whatsapp", tags=["whatsapp"])


def whatsapp_enabled() -> bool:
    return bool(settings.whatsapp_token and settings.whatsapp_phone_id)


@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(default="", alias="hub.mode"),
    token: str = Query(default="", alias="hub.verify_token"),
    challenge: str = Query(default="", alias="hub.challenge"),
):
    """Meta's one-time subscription handshake."""
    if (
        mode == "subscribe"
        and settings.whatsapp_verify_token
        and token == settings.whatsapp_verify_token
    ):
        return PlainTextResponse(challenge)
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Verification failed")


def extract_text_messages(payload: dict) -> list[dict]:
    """Pull the plain-text messages out of Meta's nested webhook payload.
    Returns [{"from": <phone>, "text": <body>}, ...]."""
    out: list[dict] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                if msg.get("type") == "text":
                    body = str(msg.get("text", {}).get("body", "")).strip()
                    sender = str(msg.get("from", "")).strip()
                    if body and sender:
                        out.append({"from": sender, "text": body[:2000]})
    return out


async def _daily_quota_ok(phone: str) -> bool:
    """Per-phone daily cap so a single number can't drain the LLM budget."""
    try:
        r = aioredis.from_url(settings.redis_url)
        key = f"avokatim:wa:{phone}"
        used = await r.incr(key)
        if used == 1:
            await r.expire(key, 24 * 3600)
        await r.aclose()
        return used <= settings.whatsapp_daily_limit
    except Exception:
        logger.warning("WhatsApp quota check unavailable — allowing")
        return True


async def send_whatsapp_text(to: str, text: str) -> bool:
    """Reply via the Graph API. No credentials -> log-only (stub mode)."""
    if not whatsapp_enabled():
        logger.info("WhatsApp stub (no credentials): would reply to %s: %.80s", to, text)
        return False
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.whatsapp_api_base}/{settings.whatsapp_phone_id}/messages",
            headers={"Authorization": f"Bearer {settings.whatsapp_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text[:4000]},
            },
        )
        if resp.status_code >= 400:
            logger.warning("WhatsApp send failed (%s): %s", resp.status_code, resp.text[:300])
            return False
    return True


async def _answer_message(sender: str, text: str) -> None:
    """Ask Ava (grounded in the XK corpus) and reply. Runs in background —
    Meta requires the webhook to return 200 quickly."""
    from app.api.marketplace import AvaAskIn, _ava_prepare
    from app.database import SessionLocal
    from app.llm import get_provider

    if not await _daily_quota_ok(sender):
        await send_whatsapp_text(
            sender,
            "Ke arritur kufirin ditor të pyetjeve falas. Provo nesër, ose "
            f"vazhdo në {settings.public_base_url}/ava",
        )
        return
    try:
        async with SessionLocal() as db:
            messages, _citations = await _ava_prepare(
                db, AvaAskIn(question=text, history=[], session_id=None)
            )
        provider = get_provider(None)
        result = await provider.chat(messages)
        answer = result.content.strip()
    except Exception as exc:
        logger.warning("WhatsApp Ava answer failed: %s", exc)
        answer = (
            "Ava nuk është e disponueshme për momentin. Provo përsëri më vonë "
            f"ose shkruaj në {settings.public_base_url}/ava"
        )
    await send_whatsapp_text(sender, answer)


@router.post("/webhook")
async def receive_webhook(request: Request, background: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid payload")
    messages = extract_text_messages(payload)
    for msg in messages:
        background.add_task(_answer_message, msg["from"], msg["text"])
    # Always 200 — Meta retries aggressively on anything else
    return {"received": len(messages)}
