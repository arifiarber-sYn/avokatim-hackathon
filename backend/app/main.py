import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    assistant,
    auth,
    billing,
    calendar_feed,
    collab,
    contacts,
    corpus,
    deadlines,
    documents,
    firm,
    imports,
    intake,
    matters,
    platform,
    portal,
    push,
    reports,
    team,
    templates,
)
from app.config import settings
from app.database import SessionLocal
from app.seeds import seed_jurisdictions
from app.services.notifications import reminder_loop

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.documents_dir.mkdir(parents=True, exist_ok=True)
    async with SessionLocal() as db:
        await seed_jurisdictions(db)
    reminders = asyncio.create_task(reminder_loop())
    yield
    reminders.cancel()


app = FastAPI(title="BoraLaw API", version="0.1.0", lifespan=lifespan)

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
app.include_router(templates.router, prefix=api_prefix)
app.include_router(assistant.router, prefix=api_prefix)
app.include_router(corpus.router, prefix=api_prefix)
app.include_router(billing.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
app.include_router(portal.router, prefix=api_prefix)
app.include_router(team.router, prefix=api_prefix)
app.include_router(collab.router, prefix=api_prefix)
app.include_router(calendar_feed.router, prefix=api_prefix)
app.include_router(intake.public_router, prefix=api_prefix)
app.include_router(push.router, prefix=api_prefix)
app.include_router(firm.router, prefix=api_prefix)
app.include_router(imports.router, prefix=api_prefix)
app.include_router(platform.router, prefix=api_prefix)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
