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
- A name-only match is NEVER auto-approved (namesakes exist); it is surfaced
  in the operator queue as a hint instead.
- No match -> stays pending for manual review, exactly as before.
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
    """Attempt automatic approval of a pending license verification.

    Runs as a background task after (a) the lawyer/notary submits a license
    number or (b) they confirm their email. Returns True when auto-approved.
    """
    from app.database import SessionLocal

    async with SessionLocal() as db:
        user = await db.get(User, user_id)
        if user is None or user.email_verified_at is None:
            return False
        profile = (
            await db.execute(
                select(LawyerProfile).where(LawyerProfile.user_id == user.id)
            )
        ).scalar_one_or_none()
        if (
            profile is None
            or profile.verification_status != "pending"
            or not profile.oak_license_no
        ):
            return False
        tenant = await db.get(Tenant, user.tenant_id)
        profession = tenant.profession if tenant else "lawyer"

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
        await send_email(
            user.email,
            tr(loc, "verify_approved_subject", name=user.full_name),
            tr(loc, "verify_approved_body",
               name=user.full_name,
               url=f"{settings.public_base_url}/avokatet",
               founder=founder_par),
        )
        from app.services.ops_notify import notify_ops

        await notify_ops(
            "auto-verifikim",
            f"{user.full_name} u verifikua AUTOMATIKISHT (licenca {chamber} "
            f"nr. {profile.oak_license_no}; emaili {user.email} përputhet me "
            f"regjistrin publik — {match['name']}, {match['city'] or '?'}). "
            f"Tani është live në drejtori. S'kërkohet veprim.",
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
                f"Licenca {chamber} nr. {profile.oak_license_no}; emaili "
                f"{user.email} përputhet me regjistrin publik "
                f"({match['name']}, {match['city'] or '?'}).\n"
                f"Nuk kërkohet asnjë veprim — shiko te "
                f"{settings.public_base_url}/platform nëse do ta rishikosh.",
            )
        return True
