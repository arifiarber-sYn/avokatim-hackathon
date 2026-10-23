"""Card payments behind a provider abstraction.

The rest of the app only ever calls `payments_enabled()` and
`create_payment_link(...)` — which provider fulfils the link is decided by
`settings.payments_provider`:

- "stripe": Stripe Checkout. Requires an entity registered in a Stripe
  country — Stripe does NOT onboard Kosovo businesses, so this only works
  if the operator incorporates abroad.
- "raiffeisen": Raiffeisen Bank Kosovo Payment Gateway (the realistic local
  rail: Visa/Mastercard + Apple/Google Pay). The adapter below is a skeleton
  wired to config; the exact endpoint paths/fields are finalized against the
  merchant API docs Raiffeisen provides after the e-commerce application
  (see docs/integrimet/raiffeisen-pagesat.md for the owner's steps).

A provider counts as enabled only when its credentials are configured, so an
empty .env keeps card payments cleanly disabled and the bank-transfer flow
(manual pay-by-link on invoices + operator marks paid) carries the load.
"""
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
    if settings.payments_provider == "raiffeisen":
        return bool(settings.raiffeisen_api_base and settings.raiffeisen_api_key)
    return bool(settings.stripe_secret_key)


async def create_payment_link(
    *,
    invoice_id: str,
    invoice_number: str,
    amount_cents: int,
    currency: str,
    description: str,
    customer_email: str | None = None,
    metadata_key: str = "invoice_id",
    return_path: str = "/portal",
) -> tuple[str, str]:
    """Create a hosted checkout for an invoice and return
    (checkout_url, session_id). Raises RuntimeError on provider errors.
    metadata_key='platform_invoice_id' for subscription invoices,
    'booking_id' for consultations."""
    if settings.payments_provider == "raiffeisen":
        return await _raiffeisen_payment_link(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            amount_cents=amount_cents,
            currency=currency,
            description=description,
            customer_email=customer_email,
            metadata_key=metadata_key,
            return_path=return_path,
        )
    return await _stripe_payment_link(
        invoice_id=invoice_id,
        invoice_number=invoice_number,
        amount_cents=amount_cents,
        currency=currency,
        description=description,
        customer_email=customer_email,
        metadata_key=metadata_key,
        return_path=return_path,
    )


# ---------- Stripe ----------


async def _stripe_payment_link(
    *,
    invoice_id: str,
    invoice_number: str,
    amount_cents: int,
    currency: str,
    description: str,
    customer_email: str | None,
    metadata_key: str,
    return_path: str,
) -> tuple[str, str]:
    data: dict[str, str] = {
        "mode": "payment",
        "success_url": f"{settings.public_base_url}{return_path}?payment=success",
        "cancel_url": f"{settings.public_base_url}{return_path}?payment=cancelled",
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": currency.lower(),
        "line_items[0][price_data][unit_amount]": str(amount_cents),
        "line_items[0][price_data][product_data][name]": description,
        f"metadata[{metadata_key}]": invoice_id,
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


# ---------- Raiffeisen Kosovo ----------


async def _raiffeisen_payment_link(
    *,
    invoice_id: str,
    invoice_number: str,
    amount_cents: int,
    currency: str,
    description: str,
    customer_email: str | None,
    metadata_key: str,
    return_path: str,
) -> tuple[str, str]:
    """Create a hosted payment session on the Raiffeisen Payment Gateway.

    The request/response shape below follows the common hosted-checkout
    pattern of the gateway; field names must be confirmed against the
    merchant API documentation delivered with the e-commerce contract and
    adjusted here — this is the ONLY function that needs touching then.
    """
    if not (settings.raiffeisen_api_base and settings.raiffeisen_api_key):
        raise RuntimeError("Raiffeisen gateway is not configured")
    payload = {
        "merchantId": settings.raiffeisen_merchant_id,
        "amount": amount_cents,
        "currency": currency.upper(),
        "description": description,
        "orderReference": invoice_number,
        "successUrl": f"{settings.public_base_url}{return_path}?payment=success",
        "cancelUrl": f"{settings.public_base_url}{return_path}?payment=cancelled",
        "metadata": {metadata_key: invoice_id, "invoice_number": invoice_number},
    }
    if customer_email:
        payload["customerEmail"] = customer_email
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.raiffeisen_api_base.rstrip('/')}/checkout/sessions",
            json=payload,
            headers={"Authorization": f"Bearer {settings.raiffeisen_api_key}"},
        )
    if resp.status_code >= 400:
        raise RuntimeError(f"Raiffeisen gateway error: {resp.text[:300]}")
    session = resp.json()
    url = session.get("checkoutUrl") or session.get("url")
    session_id = session.get("sessionId") or session.get("id", "")
    if not url:
        raise RuntimeError("Raiffeisen gateway returned no checkout URL")
    return url, session_id


def verify_raiffeisen_callback(payload: bytes, signature_header: str) -> dict | None:
    """Verify the gateway's payment callback with the shared HMAC secret.
    Mirrors the Stripe verifier so the billing webhook can dispatch on
    provider. Header scheme to confirm against the merchant docs."""
    if not settings.raiffeisen_callback_secret:
        return None
    expected = hmac.new(
        settings.raiffeisen_callback_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header.strip().lower()):
        logger.warning("Raiffeisen callback signature mismatch")
        return None
    return json.loads(payload)
