"""Open Agent 2026 endpoints: Meterless usage accounting for the UI.

Read-only on purpose: the numbers come from the JSONL the adapter writes on
every local-model call, so the UI can say what an answer cost without trusting
a second source. No writes, no DB, no provider calls.
"""
from fastapi import APIRouter, Depends

from app.adapters.meterless import summarize
from app.config import settings
from app.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/hackathon", tags=["hackathon"])


@router.get("/usage")
async def usage(last: int = 20, user: User = Depends(get_current_user)) -> dict:
    """Aggregate of data/evidence/usage.jsonl: calls, tokens, cost, last records."""
    data = summarize(settings.hackathon_usage_log, last=max(1, min(last, 200)))
    data["hackathon_mode"] = settings.hackathon_mode
    data["meterless_configured"] = bool(settings.meterless_base_url)
    data["price_in_per_mtok"] = settings.meterless_price_in_per_mtok
    data["price_out_per_mtok"] = settings.meterless_price_out_per_mtok
    return data
