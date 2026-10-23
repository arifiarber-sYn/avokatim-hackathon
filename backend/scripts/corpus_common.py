"""Shared helpers for the corpus importer scripts (D-059 F2).

The importers used to list existing docs through GET /corpus, which returns
the full document list as JSON — fine at 15k docs, minutes at 100k+. These
helpers talk to the DB directly (scripts run on the same machine) and leave
the write path on the API so chunking/embedding/audit stay in one place.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Jurisdiction, LegalCorpusDoc, User  # noqa: E402
from app.security import create_access_token  # noqa: E402


async def api_token() -> str:
    """Bearer token of the first admin — the importers write via the API."""
    async with SessionLocal() as db:
        owner = (
            await db.execute(select(User).where(User.role == "admin").limit(1))
        ).scalars().first()
        return create_access_token(str(owner.id), str(owner.tenant_id))


async def existing_references(jurisdiction_code: str) -> set[str]:
    """All non-null references already in the corpus for one jurisdiction,
    read straight from the DB (one indexed scan, no API JSON roundtrip)."""
    async with SessionLocal() as db:
        rows = await db.execute(
            select(LegalCorpusDoc.reference)
            .join(Jurisdiction, Jurisdiction.id == LegalCorpusDoc.jurisdiction_id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                LegalCorpusDoc.reference.isnot(None),
            )
        )
        return {r for (r,) in rows}


async def existing_reference_ids(jurisdiction_code: str) -> dict[str, str]:
    """reference -> doc id for one jurisdiction (for --force re-index:
    DELETE the old doc before re-importing, so chunking runs fresh)."""
    async with SessionLocal() as db:
        rows = await db.execute(
            select(LegalCorpusDoc.reference, LegalCorpusDoc.id)
            .join(Jurisdiction, Jurisdiction.id == LegalCorpusDoc.jurisdiction_id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                LegalCorpusDoc.reference.isnot(None),
            )
        )
        return {ref: str(doc_id) for (ref, doc_id) in rows}
