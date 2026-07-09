"""Card payments via Stripe Checkout. Disabled unless stripe_secret_key is
set in backend/.env. Uses the raw HTTPS API through httpx — no SDK needed."""
import hashlib
import hmac
import json
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_STRIPE_API = "https://api.stripe.com/v1"


def payments_enabled() -> bool:
    return bool(settings.stripe_secret_key)


async def create_payment_link(
    *,
    invoice_id: str,
    invoice_number: str,
    amount_cents: int,
    currency: str,
    description: str,
    customer_email: str | None = None,
) -> tuple[str, str]:
    """Create a Stripe Checkout session for an invoice.
    Returns (checkout_url, session_id). Raises on API errors."""
    data: dict[str, str] = {
        "mode": "payment",
        "success_url": f"{settings.public_base_url}/portal?payment=success",
        "cancel_url": f"{settings.public_base_url}/portal?payment=cancelled",
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": currency.lower(),
        "line_items[0][price_data][unit_amount]": str(amount_cents),
        "line_items[0][price_data][product_data][name]": description,
        "metadata[invoice_id]": invoice_id,
        "metadata[invoice_number]": invoice_number,
    }
    if customer_email:
        data["customer_email"] = customer_email
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_STRIPE_API}/checkout/sessions",
            data=data,
            auth=(settings.stripe_secret_key, ""),
        )
    if resp.status_code >= 400:
        detail = resp.json().get("error", {}).get("message", resp.text)
        raise RuntimeError(f"Stripe error: {detail}")
    session = resp.json()
    return session["url"], session["id"]


def verify_webhook_signature(payload: bytes, signature_header: str) -> dict | None:
    """Verify a Stripe webhook signature (t=...,v1=... scheme) and return the
    parsed event, or None when the signature is invalid/stale."""
    if not settings.stripe_webhook_secret:
        return None
    parts = dict(
        p.split("=", 1) for p in signature_header.split(",") if "=" in p
    )
    timestamp = parts.get("t", "")
    candidate = parts.get("v1", "")
    if not timestamp or not candidate:
        return None
    expected = hmac.new(
        settings.stripe_webhook_secret.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, candidate):
        logger.warning("Stripe webhook signature mismatch")
        return None
    # Reject events older than 5 minutes (replay protection)
    try:
        if abs(time.time() - int(timestamp)) > 300:
            return None
    except ValueError:
        return None
    return json.loads(payload)
