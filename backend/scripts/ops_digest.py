"""Daily operations digest for the OpenClaw assistant (read-only).

Prints a JSON snapshot of the last 24h: signups, marketplace activity,
verifications waiting, feedback, overdue platform invoices, outreach batch
result and site traffic (straight from the local Umami database). The
assistant turns this into the Albanian morning report on Telegram.
"""
import asyncio
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select, text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.config import PROJECT_DIR, settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    CaseRequest,
    CitizenUser,
    ConsultBooking,
    LawyerProfile,
    PlatformFeedback,
    PlatformInvoice,
    Tenant,
    User,
)

OUTREACH_LOG = PROJECT_DIR / "data" / "outreach.log"


async def _count(db, stmt) -> int:
    return (await db.execute(stmt)).scalar_one() or 0


async def gather() -> dict:
    since = datetime.now(UTC) - timedelta(hours=24)
    out: dict = {"generated_at": datetime.now(UTC).isoformat(timespec="seconds")}

    async with SessionLocal() as db:
        # --- growth (24h) ---
        new_tenants = (
            await db.execute(
                select(Tenant.name, Tenant.profession, Tenant.created_at)
                .where(Tenant.created_at >= since)
                .order_by(Tenant.created_at)
            )
        ).all()
        out["signups_24h"] = [
            {"name": n, "profession": p} for n, p, _ in new_tenants
        ]
        out["citizen_signups_24h"] = await _count(
            db, select(func.count(CitizenUser.id)).where(CitizenUser.created_at >= since)
        )

        # --- marketplace (24h) ---
        out["cases_posted_24h"] = await _count(
            db, select(func.count(CaseRequest.id)).where(CaseRequest.created_at >= since)
        )
        out["sos_24h"] = await _count(
            db, select(func.count(CaseRequest.id)).where(
                CaseRequest.created_at >= since, CaseRequest.urgency == "sos"
            )
        )
        out["cases_claimed_24h"] = await _count(
            db, select(func.count(CaseRequest.id)).where(
                CaseRequest.claimed_at.is_not(None), CaseRequest.claimed_at >= since
            )
        )
        out["bookings_24h"] = await _count(
            db, select(func.count(ConsultBooking.id)).where(
                ConsultBooking.created_at >= since
            )
        )

        # --- needs operator attention (current state, not 24h) ---
        pending = (
            await db.execute(
                select(User.full_name, LawyerProfile.oak_license_no)
                .join(User, User.id == LawyerProfile.user_id)
                .where(LawyerProfile.verification_status == "pending")
            )
        ).all()
        out["verifications_pending"] = [
            {"name": n, "license": lic} for n, lic in pending
        ]
        out["feedback_new"] = await _count(
            db, select(func.count(PlatformFeedback.id)).where(
                PlatformFeedback.status == "new"
            )
        )
        today = datetime.now(UTC).date()
        out["invoices_overdue"] = await _count(
            db, select(func.count(PlatformInvoice.id)).where(
                PlatformInvoice.status == "issued", PlatformInvoice.due_on < today
            )
        )
        out["lawyers_verified_total"] = await _count(
            db, select(func.count(LawyerProfile.id)).where(
                LawyerProfile.verification_status == "verified"
            )
        )

    # --- outreach: last batch line from the campaign log ---
    out["outreach_last"] = None
    try:
        lines = OUTREACH_LOG.read_text(encoding="utf-8").strip().splitlines()
        interesting = [
            ln for ln in lines
            if re.search(r"(dërgua|sent|batch|SKIP|klar|done)", ln, re.IGNORECASE)
        ]
        out["outreach_last"] = (interesting or lines)[-1][-300:] if lines else None
    except FileNotFoundError:
        pass

    # --- traffic from the local Umami database (read-only) ---
    try:
        umami_url = re.sub(r"/[^/]+$", "/umami", settings.database_url)
        engine = create_async_engine(umami_url, pool_pre_ping=True)
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT count(*) AS pageviews, "
                        "count(DISTINCT session_id) AS visitors "
                        "FROM website_event "
                        "WHERE created_at >= now() - interval '24 hours' "
                        "AND event_type = 1"
                    )
                )
            ).one()
            out["traffic_24h"] = {"pageviews": row.pageviews, "visitors": row.visitors}
        await engine.dispose()
    except Exception as exc:
        out["traffic_24h"] = {"error": str(exc)[:120]}

    return out


if __name__ == "__main__":
    try:
        result = asyncio.run(gather())
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
