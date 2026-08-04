"""Telephony support endpoints (D-059 F4).

The Asterisk dialplan calls GET /api/public/phone/link over loopback right
before bridging a call into the AudioSocket gateway, so the gateway can map
the call UUID to the caller's number (AudioSocket itself only carries the
UUID). Loopback-only: Asterisk runs with network_mode host on this machine.
"""

import logging

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.services.phone_gateway import link_call

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/phone", tags=["phone"])


def _require_loopback(request: Request) -> None:
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Loopback only")


@router.get("/link")
async def phone_link(
    request: Request,
    uuid: str = Query(min_length=36, max_length=36),
    caller: str = Query(default="", max_length=64),
):
    _require_loopback(request)
    await link_call(uuid, caller or "unknown")
    return {"ok": True}
