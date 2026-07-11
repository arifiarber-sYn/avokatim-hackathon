"""LiveKit access tokens for SOS video/audio rooms.

LiveKit tokens are plain HS256 JWTs (no SDK needed): iss=API key,
sub=participant identity, and a "video" claim with the room grants.
Disabled (returns None from room_token) until LIVEKIT_API_KEY/SECRET are
set in backend/.env and the livekit container runs with the same keys.
"""
from datetime import UTC, datetime, timedelta

import jwt as pyjwt

from app.config import settings

TOKEN_TTL_MINUTES = 60 * 4  # an SOS call should never outlive this


def livekit_enabled() -> bool:
    return bool(settings.livekit_api_key and settings.livekit_api_secret)


def sos_room_name(case_request_id) -> str:
    return f"sos-{case_request_id}"


def room_token(room: str, identity: str, display_name: str) -> str | None:
    """Signed join token for one participant; None when video is disabled."""
    if not livekit_enabled():
        return None
    now = datetime.now(UTC)
    payload = {
        "iss": settings.livekit_api_key,
        "sub": identity,
        "jti": identity,
        "name": display_name,
        "nbf": int(now.timestamp()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=TOKEN_TTL_MINUTES)).timestamp()),
        "video": {
            "room": room,
            "roomJoin": True,
            "roomCreate": True,
            "canPublish": True,
            "canSubscribe": True,
        },
    }
    return pyjwt.encode(payload, settings.livekit_api_secret, algorithm="HS256")
