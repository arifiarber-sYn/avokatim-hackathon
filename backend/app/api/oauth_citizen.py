"""Social login for citizen accounts — Google, Apple (iCloud) and Meta.

Requested by the first real users: creating an account must work with the
identity they already have on their phone (Apple for iOS, Google for Android,
Meta as extra), with email/password only as the fallback.

Server-side authorization-code flow, no SDKs:

    GET  /public/oauth/providers            -> which buttons to show
    GET  /public/oauth/{provider}/start     -> 302 to the provider
    GET/POST /public/oauth/{provider}/callback
        -> exchanges the code, finds-or-creates the CitizenUser and 302s
           back to the app with the citizen JWT in the URL fragment
           (fragments never reach server logs).

Identity rules:
- The provider's stable user id (sub) is the primary key of the identity;
  an existing account with the same (verified) email is linked, not duplicated.
- Emails from Google/Apple are verified by the provider; Meta returns the
  account's confirmed email. So the account is born verified and the regular
  thank-you letter goes out immediately (COMMS.md lane A).

A provider's button appears only when its credentials are configured in
backend/.env; nothing here assumes all three exist.
"""
import base64
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import httpx
import jwt as pyjwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.jurisdictions import country_from_request, is_valid_country, public_base_url_for
from app.models import CitizenUser
from app.services.audit import log_action
from app.services.notifications import _is_test_recipient
from app.services.ops_notify import notify_ops

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/oauth", tags=["public"])

STATE_TTL_MINUTES = 10

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
APPLE_AUTH_URL = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
META_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
META_PROFILE_URL = "https://graph.facebook.com/v18.0/me"


def enabled_providers() -> list[str]:
    out = []
    if settings.oauth_google_client_id and settings.oauth_google_client_secret:
        out.append("google")
    if (
        settings.oauth_apple_client_id
        and settings.oauth_apple_team_id
        and settings.oauth_apple_key_id
        and settings.oauth_apple_private_key
    ):
        out.append("apple")
    if settings.oauth_meta_client_id and settings.oauth_meta_client_secret:
        out.append("meta")
    return out


def _redirect_uri(provider: str, country: str = "XK") -> str:
    """Callback URL the provider returns to. By default the single URI
    registered on the main host; with oauth_country_callbacks=true (D-058)
    each country host keeps the whole flow on its own origin — no visible
    cross-host hop at the last step of the provider's procedure."""
    base = (
        public_base_url_for(country)
        if settings.oauth_country_callbacks
        else settings.public_base_url
    )
    return f"{base}/api/public/oauth/{provider}/callback"


def _safe_next(path: str | None) -> str:
    """Only same-site absolute paths — never an open redirect."""
    if path and path.startswith("/") and not path.startswith("//"):
        return path
    return "/kycu"


def _make_state(locale: str, next_path: str, country: str = "XK") -> str:
    now = datetime.now(UTC)
    return pyjwt.encode(
        {"purpose": "oauth_state", "locale": locale, "next": _safe_next(next_path),
         "country": country,
         "iat": now, "exp": now + timedelta(minutes=STATE_TTL_MINUTES)},
        settings.secret_key,
        algorithm="HS256",
    )


def _read_state(state: str) -> dict:
    try:
        payload = pyjwt.decode(state, settings.secret_key, algorithms=["HS256"])
    except pyjwt.PyJWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired state")
    if payload.get("purpose") != "oauth_state":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired state")
    return payload


def _apple_client_secret() -> str:
    """Apple's 'client secret' is a short-lived ES256 JWT signed with the
    developer's .p8 key (given as PEM text or a file path in .env)."""
    key = settings.oauth_apple_private_key
    if "BEGIN" not in key:
        key = Path(key).read_text(encoding="utf-8")
    now = int(time.time())
    return pyjwt.encode(
        {"iss": settings.oauth_apple_team_id, "iat": now, "exp": now + 600,
         "aud": "https://appleid.apple.com", "sub": settings.oauth_apple_client_id},
        key,
        algorithm="ES256",
        headers={"kid": settings.oauth_apple_key_id},
    )


@router.get("/providers")
async def list_providers():
    return {"providers": enabled_providers()}


@router.get("/{provider}/start")
async def oauth_start(
    provider: str,
    request: Request,
    locale: str = "sq",
    next: str = "/kycu",
    login_hint: str = "",
):
    if provider not in enabled_providers():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not configured")
    # The originating country rides inside the signed state token; the
    # callback host follows _redirect_uri (main host, or the country host
    # once oauth_country_callbacks is on — D-058).
    country = country_from_request(request)
    state = _make_state(locale, next, country)
    redirect_uri = _redirect_uri(provider, country)
    if provider == "google":
        params = {
            "client_id": settings.oauth_google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            # Verified-email accounts only; no offline access needed
            "prompt": "select_account",
        }
        if login_hint:
            # "Vazhdo si X" (D-058): preselect the remembered account so the
            # user skips the account chooser entirely
            params["login_hint"] = login_hint[:254]
            del params["prompt"]
        return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")
    if provider == "apple":
        params = {
            "client_id": settings.oauth_apple_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "name email",
            "response_mode": "form_post",  # required by Apple when scopes are set
            "state": state,
        }
        return RedirectResponse(f"{APPLE_AUTH_URL}?{urlencode(params)}")
    params = {
        "client_id": settings.oauth_meta_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "email,public_profile",
        "state": state,
    }
    return RedirectResponse(f"{META_AUTH_URL}?{urlencode(params)}")


async def _fetch_identity(
    provider: str, code: str, user_json: str | None, country: str = "XK"
) -> dict:
    """Exchange the authorization code and return
    {sub, email, name, email_verified, picture}. Raises HTTPException on
    failure. The token exchange must present the exact redirect_uri used at
    /start, so the country from the state token is passed through."""
    redirect_uri = _redirect_uri(provider, country)
    async with httpx.AsyncClient(timeout=20) as web:
        if provider == "google":
            r = await web.post(GOOGLE_TOKEN_URL, data={
                "client_id": settings.oauth_google_client_id,
                "client_secret": settings.oauth_google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            })
            r.raise_for_status()
            access_token = r.json()["access_token"]
            r = await web.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r.raise_for_status()
            info = r.json()
            return {
                "sub": info["sub"],
                "email": (info.get("email") or "").lower(),
                "name": info.get("name") or "",
                "email_verified": bool(info.get("email_verified")),
                "picture": info.get("picture") or "",
            }
        if provider == "apple":
            r = await web.post(APPLE_TOKEN_URL, data={
                "client_id": settings.oauth_apple_client_id,
                "client_secret": _apple_client_secret(),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            })
            r.raise_for_status()
            # The id_token arrives directly from Apple's token endpoint over
            # TLS, so decoding without signature verification is safe here.
            claims = pyjwt.decode(
                r.json()["id_token"], options={"verify_signature": False}
            )
            # Apple sends the name only once, as a `user` form field on the
            # first authorization
            name = ""
            if user_json:
                import json as json_lib

                try:
                    n = json_lib.loads(user_json).get("name") or {}
                    name = " ".join(
                        p for p in (n.get("firstName"), n.get("lastName")) if p
                    )
                except (ValueError, AttributeError):
                    pass
            return {
                "sub": claims["sub"],
                "email": (claims.get("email") or "").lower(),
                "name": name,
                # Apple emails (incl. private relay) are always deliverable
                "email_verified": True,
                "picture": "",  # Apple exposes no avatar
            }
        # meta
        r = await web.get(META_TOKEN_URL, params={
            "client_id": settings.oauth_meta_client_id,
            "client_secret": settings.oauth_meta_client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        })
        r.raise_for_status()
        access_token = r.json()["access_token"]
        r = await web.get(META_PROFILE_URL, params={
            "fields": "id,name,email", "access_token": access_token,
        })
        r.raise_for_status()
        info = r.json()
        return {
            "sub": info["id"],
            "email": (info.get("email") or "").lower(),
            "name": info.get("name") or "",
            "email_verified": bool(info.get("email")),
            "picture": "",
        }


MAX_PHOTO_BYTES = 300_000


async def _fetch_photo(url: str) -> str | None:
    """Download the provider's avatar server-side and inline it as a data
    URL (D-058). The browser never talks to a third-party image host, so the
    CSP stays at img-src 'self' data: — same approach as lawyer photos."""
    if not url.startswith("https://"):
        return None
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=True) as web:
            r = await web.get(url)
            r.raise_for_status()
            ctype = (r.headers.get("content-type") or "").split(";")[0].strip()
            if not ctype.startswith("image/") or len(r.content) > MAX_PHOTO_BYTES:
                return None
            return f"data:{ctype};base64,{base64.b64encode(r.content).decode()}"
    except httpx.HTTPError:
        return None


async def _find_or_create_citizen(
    db, provider: str, ident: dict, locale: str, background: BackgroundTasks,
    country: str = "XK",
) -> CitizenUser:
    citizen = (
        await db.execute(
            select(CitizenUser).where(
                CitizenUser.oauth_provider == provider,
                CitizenUser.oauth_sub == ident["sub"],
            )
        )
    ).scalar_one_or_none()
    if citizen is not None:
        return citizen

    # Same verified email = same person -> link instead of duplicating
    if ident["email"]:
        citizen = (
            await db.execute(
                select(CitizenUser).where(CitizenUser.email == ident["email"])
            )
        ).scalar_one_or_none()
        if citizen is not None:
            citizen.oauth_provider = provider
            citizen.oauth_sub = ident["sub"]
            if citizen.email_verified_at is None and ident["email_verified"]:
                citizen.email_verified_at = datetime.now(UTC)
            await db.commit()
            return citizen

    now = datetime.now(UTC)
    citizen = CitizenUser(
        email=ident["email"],
        full_name=ident["name"] or ident["email"].split("@")[0] or "Qytetar",
        password_hash=None,
        locale=locale,
        country=country if is_valid_country(country) else "XK",
        oauth_provider=provider,
        oauth_sub=ident["sub"],
        email_verified_at=now if ident["email_verified"] else None,
        # The consent note sits next to the provider buttons in the UI
        privacy_accepted_at=now,
    )
    db.add(citizen)
    await db.flush()
    await log_action(
        db, tenant_id=None, user_id=None, action="citizen.signup_oauth",
        entity_type="citizen", entity_id=str(citizen.id),
        details={"provider": provider},
    )
    await db.commit()

    if ident["email_verified"] and not _is_test_recipient(citizen.email):
        from app.api.marketplace import _send_citizen_welcome

        background.add_task(
            _send_citizen_welcome,
            citizen.email, citizen.full_name, citizen.locale, citizen.country,
        )
        background.add_task(
            notify_ops, "regjistrim-qytetar",
            f"Qytetar i ri u regjistrua me {provider.capitalize()}: "
            f"{citizen.full_name}. Letra falënderuese iu dërgua automatikisht "
            f"— s'kërkohet veprim.",
        )
    return citizen


def _finish(next_path: str, fragment: str, country: str = "XK") -> RedirectResponse:
    # 303 turns Apple's form_post POST into a GET at the app; the user
    # returns to the country host they started from (de.avokatiim.ai / main)
    return RedirectResponse(
        f"{public_base_url_for(country)}{_safe_next(next_path)}#{fragment}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


async def _handle_callback(
    provider: str,
    code: str | None,
    state: str | None,
    error: str | None,
    user_json: str | None,
    background: BackgroundTasks,
    db,
):
    if provider not in enabled_providers():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not configured")
    payload = _read_state(state or "")
    next_path = payload.get("next") or "/kycu"
    country = payload.get("country") or "XK"
    if error or not code:  # user cancelled at the provider
        return _finish(next_path, "oauth_error=cancelled", country)
    try:
        ident = await _fetch_identity(provider, code, user_json, country)
    except (httpx.HTTPError, KeyError) as exc:
        logger.warning("OAuth %s exchange failed: %s", provider, exc)
        return _finish(next_path, "oauth_error=exchange", country)
    if not ident["email"]:
        # e.g. a Meta account without a confirmed email
        return _finish(next_path, "oauth_error=no_email", country)

    citizen = await _find_or_create_citizen(
        db, provider, ident, payload.get("locale") or "sq", background, country
    )
    if not citizen.is_active:
        return _finish(next_path, "oauth_error=disabled", country)

    # Keep the profile photo fresh on every login (people change avatars);
    # a failed download never blocks the login itself.
    if ident.get("picture"):
        photo = await _fetch_photo(ident["picture"])
        if photo and photo != citizen.photo:
            citizen.photo = photo
            await db.commit()

    from app.api.marketplace import _citizen_token

    return _finish(next_path, f"citizen_token={_citizen_token(citizen.id)}", country)


@router.get("/{provider}/callback")
async def oauth_callback_get(
    provider: str,
    background: BackgroundTasks,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await _handle_callback(provider, code, state, error, None, background, db)


@router.post("/{provider}/callback")
async def oauth_callback_post(
    provider: str,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Apple uses response_mode=form_post; the code/state/user arrive as an
    application/x-www-form-urlencoded POST body."""
    form = await request.form()
    return await _handle_callback(
        provider,
        form.get("code"),
        form.get("state"),
        form.get("error"),
        form.get("user"),
        background,
        db,
    )
