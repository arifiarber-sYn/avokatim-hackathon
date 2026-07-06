"""Retrieval over the legal corpus and matter documents.

Embeddings are computed locally (sentence-transformers, multilingual) so no
document text leaves this machine for indexing. If the optional AI extras are
not installed, search falls back to PostgreSQL trigram/ILIKE matching.
"""
import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Document, DocumentChunk, LegalCorpusChunk, LegalCorpusDoc

logger = logging.getLogger(__name__)

_model = None
_model_failed = False

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def _get_model():
    global _model, _model_failed
    if _model is None and not _model_failed:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(settings.embedding_model)
        except Exception as exc:
            _model_failed = True
            logger.warning("Embeddings unavailable, falling back to text search: %s", exc)
    return _model


def embed(texts: list[str]) -> list[list[float]] | None:
    model = _get_model()
    if model is None:
        return None
    return [v.tolist() for v in model.encode(texts, normalize_embeddings=True)]


def chunk_text(text: str) -> list[str]:
    """Split on paragraph boundaries into ~CHUNK_SIZE character chunks."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 2 > CHUNK_SIZE and current:
            chunks.append(current)
            current = current[-CHUNK_OVERLAP:] + "\n\n" + p
        else:
            current = f"{current}\n\n{p}" if current else p
    if current:
        chunks.append(current)
    return chunks


async def index_document_chunks(db: AsyncSession, document: Document) -> int:
    """(Re)index a matter document's text into chunks with embeddings."""
    if not document.text_content:
        return 0
    for old in (
        await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
    ).scalars():
        await db.delete(old)

    chunks = chunk_text(document.text_content)
    vectors = embed(chunks)
    for i, text in enumerate(chunks):
        db.add(
            DocumentChunk(
                document_id=document.id,
                seq=i,
                text=text,
                embedding=vectors[i] if vectors else None,
            )
        )
    return len(chunks)


def _query_words(query: str) -> list[str]:
    return [w.lower() for w in re.split(r"\W+", query) if len(w) > 3][:10]


def _score_rows(rows, query: str, limit: int):
    """Fallback ranking: order candidate chunks by how many query words they
    contain (any-match, not all-match)."""
    words = _query_words(query)
    scored = []
    for chunk, parent in rows:
        text = chunk.text.lower()
        score = sum(1 for w in words if w in text)
        if score > 0:
            scored.append((score, chunk, parent))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(chunk, parent) for _, chunk, parent in scored[:limit]]


async def search_corpus(
    db: AsyncSession, jurisdiction_id: uuid.UUID, query: str, limit: int = 6
) -> list[dict]:
    """Semantic (or fallback text) search over the legal corpus."""
    vectors = embed([query])
    if vectors:
        stmt = (
            select(LegalCorpusChunk, LegalCorpusDoc)
            .join(LegalCorpusDoc, LegalCorpusDoc.id == LegalCorpusChunk.doc_id)
            .where(
                LegalCorpusDoc.jurisdiction_id == jurisdiction_id,
                LegalCorpusChunk.embedding.isnot(None),
            )
            .order_by(LegalCorpusChunk.embedding.cosine_distance(vectors[0]))
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
    else:
        rows = []
    if not rows:
        # No embeddings available (model missing, or chunks indexed before it
        # was installed) — fall back to word-overlap scoring.
        stmt = (
            select(LegalCorpusChunk, LegalCorpusDoc)
            .join(LegalCorpusDoc, LegalCorpusDoc.id == LegalCorpusChunk.doc_id)
            .where(LegalCorpusDoc.jurisdiction_id == jurisdiction_id)
            .limit(2000)
        )
        rows = _score_rows((await db.execute(stmt)).all(), query, limit)

    return [
        {
            "text": chunk.text,
            "section": chunk.section,
            "doc_title": doc.title,
            "reference": doc.reference,
        }
        for chunk, doc in rows
    ]


async def search_matter_documents(
    db: AsyncSession, matter_id: uuid.UUID, query: str, limit: int = 6
) -> list[dict]:
    vectors = embed([query])
    base = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.matter_id == matter_id, Document.is_latest.is_(True))
    )
    if vectors:
        stmt = (
            base.where(DocumentChunk.embedding.isnot(None))
            .order_by(DocumentChunk.embedding.cosine_distance(vectors[0]))
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
    else:
        rows = []
    if not rows:
        rows = _score_rows((await db.execute(base.limit(2000))).all(), query, limit)

    return [
        {"text": chunk.text, "doc_title": doc.filename, "document_id": str(doc.id)}
        for chunk, doc in rows
    ]
