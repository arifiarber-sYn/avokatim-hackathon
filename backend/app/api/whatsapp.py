"""Ava over WhatsApp (Meta Business Cloud API).

Built as a testable stub: the webhook handshake and message parsing work
without any Meta credentials; the actual reply is sent only when
`whatsapp_token` + `whatsapp_phone_id` are configured in backend/.env.
Setup steps for the owner are documented in docs/integrimet/whatsapp.md.
"""
import hashlib
import hmac
import json
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
    """24/7 receptionist (D-054 F4): first give the intake flow a chance —
    "RAST" starts a guided case posting that ends on the marketplace with
    consultation slots offered. Otherwise: Ava Q&A grounded in the corpus.
    Runs in background — Meta requires the webhook to return 200 quickly."""
    from app.api.marketplace import AvaAskIn, _ava_prepare
    from app.database import SessionLocal
    from app.i18n import tr
    from app.jurisdictions import public_base_url_for
    from app.llm import get_provider
    from app.services.wa_intake import (
        daily_hint,
        handle_intake_message,
        sender_country_locale,
    )

    # Country/language follow the sender's phone prefix (D-055): a +49
    # number gets German replies, the DE corpus and de.avokatiim.ai links.
    country, locale = sender_country_locale(sender)
    base_url = public_base_url_for(country)

    try:
        intake_reply = await handle_intake_message(sender, text)
    except Exception as exc:
        logger.warning("WhatsApp intake flow failed: %s", exc)
        intake_reply = None
    if intake_reply is not None:
        await send_whatsapp_text(sender, intake_reply)
        return

    if not await _daily_quota_ok(sender):
        await send_whatsapp_text(sender, tr(locale, "wa_quota", url=base_url))
        return
    try:
        async with SessionLocal() as db:
            messages, _citations = await _ava_prepare(
                db,
                AvaAskIn(question=text, history=[], session_id=None, locale=locale),
                country=country,
            )
        provider = get_provider(None)
        result = await provider.chat(messages)
        answer = result.content.strip()
    except Exception as exc:
        logger.warning("WhatsApp Ava answer failed: %s", exc)
        answer = tr(locale, "wa_unavailable", url=base_url)
    answer += await daily_hint(settings.redis_url, sender, locale)
    await send_whatsapp_text(sender, answer)


def verify_hub_signature(raw_body: bytes, header: str | None) -> bool:
    """Meta signs every webhook POST with HMAC-SHA256 of the raw body using
    the App Secret. Without this check anyone who finds the URL can inject
    fake 'messages' and burn the LLM budget / spam arbitrary numbers."""
    if not settings.whatsapp_app_secret:
        # stub mode (no Meta app configured) — accept, as before
        return True
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.whatsapp_app_secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(header.removeprefix("sha256="), expected)


@router.post("/webhook")
async def receive_webhook(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not verify_hub_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid signature")
    try:
        payload = json.loads(raw)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid payload")
    messages = extract_text_messages(payload)
    for msg in messages:
        background.add_task(_answer_message, msg["from"], msg["text"])
    # Always 200 — Meta retries aggressively on anything else
    return {"received": len(messages)}
