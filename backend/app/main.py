import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    admin_tools,
    aml,
    api_tokens,
    assistant,
    auth,
    billing,
    bookings,
    calendar_feed,
    collab,
    contacts,
    corpus,
    deadlines,
    documents,
    email_suggestions,
    evidence,
    exports,
    feedback,
    firm,
    hackathon,
    imports,
    intake,
    marketplace,
    matters,
    notifications as notifications_api,
    oauth_citizen,
    passkeys,
    phone,
    platform,
    portal,
    privacy,
    public_tools,
    push,
    reports,
    search,
    subscription,
    tasks,
    team,
    templates,
    voice,
    whatsapp,
)
from app.config import settings
from app.database import SessionLocal
from app.seeds import seed_jurisdictions
from app.services.email_ingest import email_ingest_loop
from app.services.notifications import reminder_loop
from app.services.platform_billing import billing_loop

logging.basicConfig(level=logging.INFO)

# Error tracking (D-054 F6): self-hosted GlitchTip — everything stays local.
# No PII, no request bodies; unhandled exceptions + explicit captures only.
if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        send_default_pii=False,
        traces_sample_rate=0,
        environment="production",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.documents_dir.mkdir(parents=True, exist_ok=True)
    async with SessionLocal() as db:
        await seed_jurisdictions(db)
    reminders = asyncio.create_task(reminder_loop())
    email_ingest = asyncio.create_task(email_ingest_loop())
    billing = asyncio.create_task(billing_loop())
    # Telephony-KI (D-059 F4): AudioSocket gateway for the sipgate trunk
    phone_task = None
    if settings.phone_gateway_enabled:
        from app.services.phone_gateway import serve as phone_serve

        phone_task = asyncio.create_task(phone_serve())
    yield
    reminders.cancel()
    email_ingest.cancel()
    billing.cancel()
    if phone_task:
        phone_task.cancel()


app = FastAPI(title="AvokatIM API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(contacts.router, prefix=api_prefix)
app.include_router(matters.router, prefix=api_prefix)
app.include_router(intake.router, prefix=api_prefix)
app.include_router(deadlines.router, prefix=api_prefix)
app.include_router(documents.router, prefix=api_prefix)
app.include_router(email_suggestions.router, prefix=api_prefix)
app.include_router(templates.router, prefix=api_prefix)
app.include_router(assistant.router, prefix=api_prefix)
app.include_router(corpus.router, prefix=api_prefix)
app.include_router(billing.router, prefix=api_prefix)
app.include_router(billing.public_router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
app.include_router(portal.router, prefix=api_prefix)
app.include_router(team.router, prefix=api_prefix)
app.include_router(collab.router, prefix=api_prefix)
app.include_router(calendar_feed.router, prefix=api_prefix)
app.include_router(intake.public_router, prefix=api_prefix)
app.include_router(push.router, prefix=api_prefix)
app.include_router(api_tokens.router, prefix=api_prefix)
app.include_router(firm.router, prefix=api_prefix)
app.include_router(exports.router, prefix=api_prefix)
app.include_router(imports.router, prefix=api_prefix)
app.include_router(platform.router, prefix=api_prefix)
app.include_router(tasks.router, prefix=api_prefix)
app.include_router(search.router, prefix=api_prefix)
app.include_router(admin_tools.router, prefix=api_prefix)
app.include_router(privacy.router, prefix=api_prefix)
app.include_router(aml.router, prefix=api_prefix)
app.include_router(marketplace.router, prefix=api_prefix)
app.include_router(marketplace.public_router, prefix=api_prefix)
app.include_router(oauth_citizen.router, prefix=api_prefix)
app.include_router(subscription.router, prefix=api_prefix)
app.include_router(voice.router, prefix=api_prefix)
app.include_router(whatsapp.router, prefix=api_prefix)
app.include_router(phone.router, prefix=api_prefix)
app.include_router(public_tools.router, prefix=api_prefix)
app.include_router(bookings.router, prefix=api_prefix)
app.include_router(bookings.public_router, prefix=api_prefix)
app.include_router(evidence.router, prefix=api_prefix)
app.include_router(hackathon.router, prefix=api_prefix)
app.include_router(evidence.lawyer_router, prefix=api_prefix)
app.include_router(feedback.public_router, prefix=api_prefix)
app.include_router(feedback.admin_router, prefix=api_prefix)
app.include_router(notifications_api.router, prefix=api_prefix)
app.include_router(passkeys.router, prefix=api_prefix)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
