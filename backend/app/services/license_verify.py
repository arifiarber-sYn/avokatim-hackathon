"""Automatic license verification against the public professional registries.

The trust gate of the directory used to be fully manual (the operator checked
oak-ks.org by hand). Both chambers publish their member registries with email
addresses, and we keep local copies (data/oak_registry.csv from
scrape_oak_registry.py, data/notaries.json from scrape_onk_registry.py), so
the check can be automated with a conservative rule:

- AUTO-APPROVE only when the signup email matches a registry entry exactly
  AND the account has confirmed control of that mailbox (email_verified_at).
  Owning the inbox that the chamber itself publishes for a member is the
  strongest identity proof available without an official API.
- The chamber registries do not publish license numbers, so a typed license
  number adds nothing to the email proof — verification therefore requires
  NO extra step from the lawyer: confirming the email is enough (owner's
  call, 2026-07-31). The license number stays an optional profile field.
- A name-only match is NEVER auto-approved (namesakes exist); it is surfaced
  in the operator queue as a hint instead.
- No match -> stays pending for manual review, exactly as before.

Germany (D-034): the official BRAV registry (bea-brak.de/bravsearch) publishes
NO email addresses, so the email proof does not exist there. German lawyers
are never auto-approved; instead the operator/Halim gets a notification with
a prefilled BRAV search link for a one-click manual approval in /platform.
"""
import csv
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import PROJECT_DIR, settings
from app.models import LawyerProfile, Tenant, User

logger = logging.getLogger(__name__)

OAK_REGISTRY_FILE: Path = PROJECT_DIR / "data" / "oak_registry.csv"
_oak_cache: dict = {"mtime": None, "rows": []}

# Public search of the Bundesweites Amtliches Anwaltsverzeichnis. No API and
# no emails — used as a one-click link for the human/Halim approval step.
BRAV_SEARCH_URL = "https://bravsearch.bea-brak.de/bravsearch/"


def brav_search_hint(full_name: str) -> str:
    return f"BRAV: {BRAV_SEARCH_URL} (kërko: {full_name})"


def _norm_name(name: str) -> str:
    return " ".join(name.lower().replace("ë", "e").replace("ç", "c").split())


def load_oak_registry() -> list[dict]:
    """Lawyer registry scraped from oak-ks.org (scrape_oak_registry.py);
    cached in memory and reloaded when the file changes."""
    try:
        mtime = OAK_REGISTRY_FILE.stat().st_mtime
    except FileNotFoundError:
        return []
    if _oak_cache["mtime"] != mtime:
        with OAK_REGISTRY_FILE.open(encoding="utf-8") as fh:
            _oak_cache["rows"] = list(csv.DictReader(fh))
        _oak_cache["mtime"] = mtime
    return _oak_cache["rows"]


def registry_match(profession: str, full_name: str, email: str) -> dict | None:
    """Best-effort match against the public registry of the profession's
    chamber: exact email first, then normalized full-name equality."""
    email = (email or "").strip().lower()
    name = _norm_name(full_name or "")

    if profession == "notary":
        from app.api.public_tools import _load_notaries

        entries = [
            {"name": n.get("name", ""), "email": n.get("email", ""), "city": n.get("city")}
            for n in _load_notaries().get("notaries", [])
        ]
    else:
        entries = [
            {"name": r.get("name", ""), "email": r.get("email", ""), "city": r.get("city")}
            for r in load_oak_registry()
        ]

    for e in entries:
        if email and e["email"].strip().lower() == email:
            return {"name": e["name"], "city": e.get("city"), "matched_by": "email"}
    for e in entries:
        if name and _norm_name(e["name"]) == name:
            return {"name": e["name"], "city": e.get("city"), "matched_by": "name"}
    return None


async def try_auto_verify(user_id) -> bool:
    """Attempt automatic approval of a lawyer/notary verification.

    Runs as a background task after (a) the account confirms its email or
    (b) a license number is submitted/changed. A confirmed registry email is
    sufficient on its own — the profile row is created here if the lawyer
    has not opened onboarding yet. Returns True when auto-approved.
    """
    from app.database import SessionLocal

    async with SessionLocal() as db:
        user = await db.get(User, user_id)
        if user is None or user.email_verified_at is None:
            return False
        tenant = await db.get(Tenant, user.tenant_id)
        if tenant is None or tenant.profession not in ("lawyer", "notary"):
            return False
        profession = tenant.profession
        profile = (
            await db.execute(
                select(LawyerProfile).where(LawyerProfile.user_id == user.id)
            )
        ).scalar_one_or_none()
        if profile is None:
            # Not onboarded yet — attach the verification now; the profile
            # stays invisible until the lawyer publishes it themselves.
            profile = LawyerProfile(tenant_id=user.tenant_id, user_id=user.id)
            db.add(profile)
            await db.flush()
        if profile.verification_status not in ("none", "pending"):
            # already verified, or explicitly rejected by the operator
            return False

        from app.jurisdictions import profile_for as jurisdiction_profile

        if jurisdiction_profile(tenant.country).bar_registry == "brav":
            # Germany: BRAV publishes no emails, so there is no email proof to
            # automate on. Surface a one-click search link to the operator and
            # leave the profile pending for the manual /platform approval.
            from app.services.ops_notify import notify_ops

            profile.verification_note = brav_search_hint(user.full_name)
            await db.commit()
            await notify_ops(
                "verifikim DE",
                f"Avokat gjerman për verifikim manual: {user.full_name} "
                f"({user.email}). Kontrolloje në {BRAV_SEARCH_URL} dhe "
                f"aprovoje te {settings.public_base_url}/platform",
            )
            return False

        match = registry_match(profession, user.full_name, user.email)
        if match is None or match["matched_by"] != "email":
            return False

        chamber = "ONK" if profession == "notary" else "OAK"
        profile.verification_status = "verified"
        profile.verified_at = datetime.now(UTC)
        profile.verification_note = (
            f"Auto-verifikim: emaili përputhet me regjistrin publik të {chamber}-së "
            f"({match['name']}, {match['city'] or '?'})"
        )
        if not profile.is_founder and profession == "lawyer":
            from app.api.platform import FOUNDER_LIMIT

            verified_count = (
                await db.execute(
                    select(func.count(LawyerProfile.id)).where(
                        LawyerProfile.verification_status == "verified",
                        LawyerProfile.id != profile.id,
                    )
                )
            ).scalar_one()
            if verified_count < FOUNDER_LIMIT:
                profile.is_founder = True

        from app.services.audit import log_action

        await log_action(
            db, tenant_id=profile.tenant_id, user_id=None,
            action="platform.verification_auto", entity_type="lawyer_profile",
            entity_id=str(profile.id),
            details={
                "license": profile.oak_license_no,
                "matched_by": "email",
                "registry": chamber,
            },
        )
        await db.commit()
        logger.info(
            "Auto-verified %s license %s for %s (registry email match)",
            chamber, profile.oak_license_no, user.email,
        )

        from app.i18n import pick_locale, tr
        from app.services.notifications import send_email

        loc = pick_locale(user.locale)
        # Warm thank-you letter — the moment they officially join the platform
        founder_par = (
            tr(loc, "verify_approved_founder") + "\n\n" if profile.is_founder else ""
        )
        profile_url = f"{settings.public_base_url}/avokatet/{profile.id}"
        settings_url = f"{settings.public_base_url}/settings"
        await send_email(
            user.email,
            tr(loc, "verify_approved_subject", name=user.full_name),
            tr(loc, "verify_approved_body",
               name=user.full_name,
               url=profile_url,
               settings_url=settings_url,
               founder=founder_par),
        )
        from app.services.ops_notify import notify_ops

        license_txt = (
            f"licenca {chamber} nr. {profile.oak_license_no}; "
            if profile.oak_license_no
            else f"anëtar i regjistrit {chamber}; "
        )
        await notify_ops(
            "auto-verifikim",
            f"{user.full_name} u verifikua AUTOMATIKISHT ({license_txt}"
            f"emaili {user.email} përputhet me "
            f"regjistrin publik — {match['name']}, {match['city'] or '?'}). "
            f"S'kërkohet veprim.",
        )
        # FYI to the operator — no action needed, but keep them in the loop
        operators = (
            await db.execute(
                select(User).where(User.is_superadmin.is_(True), User.is_active.is_(True))
            )
        ).scalars().all()
        for op in operators:
            await send_email(
                op.email,
                f"AvokatIM — Verifikim automatik {chamber}: {user.full_name}",
                f"{user.full_name} u verifikua AUTOMATIKISHT.\n"
                f"{license_txt.capitalize().rstrip('; ')}. Emaili "
                f"{user.email} përputhet me regjistrin publik "
                f"({match['name']}, {match['city'] or '?'}).\n"
                f"Nuk kërkohet asnjë veprim — shiko te "
                f"{settings.public_base_url}/platform nëse do ta rishikosh.",
            )
        return True
