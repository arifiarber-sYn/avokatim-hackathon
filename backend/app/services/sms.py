"""SMS notifications through a Twilio-compatible REST API. Disabled unless
sms_account_sid is set in backend/.env. Used for hearing reminders to clients."""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def sms_enabled() -> bool:
    return bool(settings.sms_account_sid and settings.sms_auth_token and settings.sms_from)


async def send_sms(to: str, body: str) -> bool:
    """Send an SMS. Returns True on success; never raises."""
    if not sms_enabled():
        return False
    url = (
        f"{settings.sms_api_base}/2010-04-01/Accounts/"
        f"{settings.sms_account_sid}/Messages.json"
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                data={"To": to, "From": settings.sms_from, "Body": body[:1500]},
                auth=(settings.sms_account_sid, settings.sms_auth_token),
            )
        if resp.status_code >= 400:
            logger.warning("SMS to %s failed: %s", to, resp.text[:300])
            return False
        return True
    except Exception as exc:
        logger.warning("SMS to %s failed: %s", to, exc)
        return False
