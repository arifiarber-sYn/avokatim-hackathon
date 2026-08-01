"""Legal corpus management: the lawyer (or a future importer) uploads laws /
regulations, which get chunked, embedded and become the RAG knowledge base."""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.jurisdictions import is_valid_region, jurisdiction_row_for_tenant
from app.deps import get_current_user, require_superadmin
from app.models import Jurisdiction, LegalCorpusChunk, LegalCorpusDoc, User
from app.services import rag
from app.services.audit import log_action

router = APIRouter(prefix="/corpus", tags=["corpus"])

# Article headers in the five official gazette languages + Chinese:
# sq "Neni 176", sr/bs "Član 5" (also "Clan" when diacritics are lost in
# extraction), tr "Madde 5", en "Article 5", zh "第一条",
# de "§ 573" / "Art 13" / "Artikel 79" (gesetze-im-internet enbez markers).
# Judgment part headings (Leitsatz/Tenor/Gründe…) match only when the line is
# exactly the heading, so ordinary law text never trips them.
_SECTION_RE = re.compile(
    r"^(Neni\s+\d+[a-z]?|[ČC]lan\s+\d+[a-z]?|Madde\s+\d+[a-z]?"
    r"|Article\s+\d+[a-z]?|第[一二三四五六七八九十百千0-9]+条"
    r"|§\s*\d+[a-z]?\b|Art(?:ikel)?\.?\s+\d+[a-z]?\b"
    r"|(?:Leitsatz|Orientierungssatz|Tenor|Tatbestand"
    r"|Entscheidungsgründe|Gründe|Abweichende Meinung)(?=\s*$))",
    re.IGNORECASE,
)


class CorpusDocIn(BaseModel):
    jurisdiction_code: str = "XK"
    title: str = Field(min_length=2, max_length=500)
    doc_type: str = "law"
    reference: str | None = None
    source_url: str | None = None
    language: str = "sq"
    # Sub-national scope (DE Landesrecht: Bundesland code); None = federal
    region: str | None = Field(default=None, max_length=8)
    text: str = Field(min_length=10)


class CorpusDocOut(BaseModel):
    id: uuid.UUID
    title: str
    doc_type: str
    reference: str | None
    language: str
    region: str | None = None
    chunk_count: int = 0

    model_config = {"from_attributes": True}


def _split_by_articles(text: str) -> list[tuple[str | None, str]]:
    """Split legal text on article boundaries; falls back to size-based chunks."""
    lines = text.splitlines()
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    for line in lines:
        match = _SECTION_RE.match(line.strip())
        if match:
            sections.append((match.group(1), [line]))
        else:
            sections[-1][1].append(line)

    result: list[tuple[str | None, str]] = []
    for section, body_lines in sections:
        body = "\n".join(body_lines).strip()
        if not body:
            continue
        if len(body) > rag.CHUNK_SIZE * 2:
            for piece in rag.chunk_text(body):
                result.append((section, piece))
        else:
            result.append((section, body))
    return result


@router.get("", response_model=list[CorpusDocOut])
async def list_corpus(
    jurisdiction_code: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if jurisdiction_code:
        jurisdiction = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == jurisdiction_code))
        ).scalar_one_or_none()
        if jurisdiction is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Jurisdiction not found")
    else:
        jurisdiction = await jurisdiction_row_for_tenant(db, user.tenant_id)
    docs = (
        await db.execute(
            select(LegalCorpusDoc).where(LegalCorpusDoc.jurisdiction_id == jurisdiction.id)
        )
    ).scalars().all()
    out = []
    for doc in docs:
        count = (
            await db.execute(
                select(func.count(LegalCorpusChunk.id)).where(
                    LegalCorpusChunk.doc_id == doc.id
                )
            )
        ).scalar_one()
        item = CorpusDocOut.model_validate(doc)
        item.chunk_count = count
        out.append(item)
    return out


@router.post("", response_model=CorpusDocOut, status_code=status.HTTP_201_CREATED)
async def add_corpus_doc(
    body: CorpusDocIn,
    user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    jurisdiction = (
        await db.execute(
            select(Jurisdiction).where(Jurisdiction.code == body.jurisdiction_code)
        )
    ).scalar_one_or_none()
    if jurisdiction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jurisdiction not found")
    region = body.region.upper() if body.region else None
    if region and not is_valid_region(body.jurisdiction_code, region):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown region code")

    doc = LegalCorpusDoc(
        jurisdiction_id=jurisdiction.id,
        title=body.title,
        doc_type=body.doc_type,
        reference=body.reference,
        source_url=body.source_url,
        language=body.language,
        region=region,
    )
    db.add(doc)
    await db.flush()

    pieces = _split_by_articles(body.text)
    vectors = rag.embed([p[1] for p in pieces])
    ts_config = rag.ts_config_for(doc.language)
    for i, (section, text) in enumerate(pieces):
        db.add(
            LegalCorpusChunk(
                doc_id=doc.id,
                seq=i,
                section=section,
                text=text,
                embedding=vectors[i] if vectors else None,
                tsv=func.to_tsvector(ts_config, text),
            )
        )

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="corpus.add",
        entity_type="corpus_doc", entity_id=str(doc.id),
        details={"title": body.title, "chunks": len(pieces)},
    )
    await db.commit()
    out = CorpusDocOut.model_validate(doc)
    out.chunk_count = len(pieces)
    return out


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_corpus_doc(
    doc_id: uuid.UUID,
    user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(LegalCorpusDoc, doc_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    await db.delete(doc)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="corpus.delete",
        entity_type="corpus_doc", entity_id=str(doc_id),
    )
    await db.commit()
