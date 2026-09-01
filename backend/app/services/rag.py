"""Retrieval over the legal corpus and matter documents.

Embeddings are computed locally (sentence-transformers, multilingual) so no
document text leaves this machine for indexing. If the optional AI extras are
not installed, search falls back to PostgreSQL trigram/ILIKE matching.
"""
import logging
import re
import uuid

from sqlalchemy import func, or_, select
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


# German sentences start with a capital letter, so this splits after .!?
# only before an uppercase letter — never inside abbreviations like "Art. 1",
# "Abs. 2", "Nr. 5", "z. B." (those are followed by digits/lowercase).
_SENT_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ])")


def _split_paragraph(p: str) -> list[str]:
    """Split one oversized paragraph into ~CHUNK_SIZE pieces.

    German legal texts (BGB sections, judgment "Gründe") routinely contain
    multi-kilobyte single paragraphs. Paragraph boundaries alone are not
    enough: split on sentence boundaries first, then hard-cap at CHUNK_SIZE
    for sentences that are themselves oversized (DE launch-gate item 3,
    2026-08-23: max prompt 15.3K tokens vs 13.1K budget).
    """
    pieces: list[str] = []
    current = ""
    for sentence in _SENT_BOUNDARY.split(p):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current) + len(sentence) + 1 > CHUNK_SIZE and current:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}" if current else sentence
        while len(current) > CHUNK_SIZE:  # one enormous sentence
            cut = current.rfind(" ", 0, CHUNK_SIZE)
            if cut < CHUNK_SIZE // 2:  # no usable word boundary — hard cut
                cut = CHUNK_SIZE
            pieces.append(current[:cut].strip())
            current = current[cut:].strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str) -> list[str]:
    """Split on paragraph boundaries into ~CHUNK_SIZE character chunks.

    Paragraphs longer than CHUNK_SIZE (common in German legal prose) are
    split further via ``_split_paragraph`` so no single chunk exceeds the
    embedding/LLM context budget.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        if len(p) > CHUNK_SIZE:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_paragraph(p))
            continue
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
                # 'simple' config: matter documents are multilingual and carry
                # no language column — exact words only, no stemming.
                tsv=func.to_tsvector("simple", text),
            )
        )
    return len(chunks)


def ts_config_for(language: str | None) -> str:
    """Postgres text-search config per corpus language: German gets stemming;
    Albanian & friends have no built-in config, so 'simple' (exact words)."""
    return "german" if language == "de" else "simple"


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
    db: AsyncSession,
    jurisdiction_id: uuid.UUID,
    query: str,
    limit: int = 6,
    language: str | None = None,
    fallback_language: str | None = None,
    region: str | None = None,
) -> list[dict]:
    """Semantic (or fallback text) search over the legal corpus.

    When `language` is given, the search runs over that language's official
    texts plus the jurisdiction's complete corpus language as fallback
    (sq for Kosovo, de for Germany — see JurisdictionProfile, D-034); cosine
    ranking naturally prefers the chunks that match the query's language.
    When `fallback_language` is None it is resolved from the jurisdiction.

    `region` widens the scope to a Bundesland's Landesrecht (D-035): federal
    docs (region IS NULL) are always searched; docs of OTHER regions never.
    """
    if fallback_language is None:
        from app.jurisdictions import profile_for
        from app.models import Jurisdiction

        jur = await db.get(Jurisdiction, jurisdiction_id)
        fallback_language = profile_for(
            getattr(jur, "code", None)
        ).corpus_fallback_language
    lang_filter = (
        LegalCorpusDoc.language.in_([language, fallback_language])
        if language and language != fallback_language
        else LegalCorpusDoc.language == fallback_language
    )
    region_filter = (
        LegalCorpusDoc.region.is_(None)
        if region is None
        else or_(LegalCorpusDoc.region.is_(None), LegalCorpusDoc.region == region)
    )
    scope = (
        select(LegalCorpusChunk, LegalCorpusDoc)
        .join(LegalCorpusDoc, LegalCorpusDoc.id == LegalCorpusChunk.doc_id)
        .where(
            LegalCorpusDoc.jurisdiction_id == jurisdiction_id,
            lang_filter,
            region_filter,
        )
    )
    # Hybrid retrieval (D-042): dense cosine + two full-text legs, fused with
    # Reciprocal Rank Fusion. Vector search finds paraphrases; the AND leg
    # (plainto, all terms) nails full phrases when they occur verbatim; the
    # rare-word OR leg keeps only distinctive terms (IDF-style: common words
    # like "BGB"/"Anspruch" would flood the ranking with judgment chunks) and
    # prefix-matches them so "Berufung" also finds "Berufungsfrist".
    # Either leg alone still works if the others are empty.
    fetch_n = max(limit * 4, 12)
    ts_config = ts_config_for(fallback_language)
    vec_rows: list = []
    vectors = embed([query])
    if vectors:
        stmt = (
            scope.where(LegalCorpusChunk.embedding.isnot(None))
            .order_by(LegalCorpusChunk.embedding.cosine_distance(vectors[0]))
            .limit(fetch_n)
        )
        vec_rows = (await db.execute(stmt)).all()

    async def _fts(ts_query) -> list:
        stmt = (
            scope.where(
                LegalCorpusChunk.tsv.isnot(None),
                LegalCorpusChunk.tsv.op("@@")(ts_query),
            )
            .order_by(func.ts_rank(LegalCorpusChunk.tsv, ts_query).desc())
            .limit(fetch_n)
        )
        return (await db.execute(stmt)).all()

    fts_rows = await _fts(func.plainto_tsquery(ts_config, query))
    rare = await _rare_query_words(db, jurisdiction_id, query, ts_config)
    rare_rows = (
        await _fts(func.to_tsquery(ts_config, " | ".join(f"{w}:*" for w in rare)))
        if rare
        else []
    )

    if vec_rows or fts_rows or rare_rows:
        # Statutes stay the primary ground; but when the question is openly
        # about case law, judgments may take up to half the slots (D-059 F2)
        cap = limit // 2 if _wants_case_law(query) else limit // 3
        rows = _rrf_fuse(
            [vec_rows, fts_rows, rare_rows], limit,
            max_judgments=max(1, cap),
        )
    else:
        # No embeddings and no FTS hits (model missing / exotic query) —
        # fall back to word-overlap scoring.
        rows = _score_rows((await db.execute(scope.limit(2000))).all(), query, limit)

    return [
        {
            "text": chunk.text,
            "section": chunk.section,
            "doc_title": doc.title,
            "reference": doc.reference,
            "region": doc.region,
            "doc_type": doc.doc_type,
        }
        for chunk, doc in rows
    ]


# Signals that the user is explicitly after case law, not statutes —
# court names, decision words (de/sq/en/sr) and Aktenzeichen patterns.
_CASE_LAW_RE = re.compile(
    r"\b(Urteil|Beschluss|Rechtsprechung|entschieden|BGH|BAG|BVerfG|BVerwG"
    r"|BFH|BSG|BPatG|OLG|LG|AG\s+\w+|ECLI|Aktenzeichen"
    r"|vendim\w*|praktik\w+\s+gjyqësor\w*|gjykata\s+supreme|aktgjykim\w*"
    r"|presud\w*|sudska\s+praksa|case\s+law|judgment|ruling)\b",
    re.IGNORECASE,
)


def _wants_case_law(query: str) -> bool:
    return bool(_CASE_LAW_RE.search(query))


# Words more frequent than this share of chunks carry no signal for the
# rare-word leg (e.g. "BGB" appears in every second judgment chunk).
_RARE_DF_CAP = 0.02
_RARE_MAX_WORDS = 4


async def _rare_query_words(
    db: AsyncSession, jurisdiction_id: uuid.UUID, query: str, ts_config: str
) -> list[str]:
    """The up-to-4 rarest query words (by chunk document frequency) that are
    distinctive enough to search on. Cheap: one GIN-backed count per word."""
    words = [w for w in re.findall(r"[0-9A-Za-zÀ-ÿẞ]+", query) if len(w) > 2][:10]
    if not words:
        return []
    base = select(func.count(LegalCorpusChunk.id)).join(
        LegalCorpusDoc, LegalCorpusDoc.id == LegalCorpusChunk.doc_id
    ).where(
        LegalCorpusDoc.jurisdiction_id == jurisdiction_id,
        LegalCorpusChunk.tsv.isnot(None),
    )
    total = (await db.execute(base)).scalar_one()
    if not total:
        return []
    ranked: list[tuple[int, str]] = []
    for word in words:
        df = (
            await db.execute(
                base.where(
                    LegalCorpusChunk.tsv.op("@@")(func.to_tsquery(ts_config, f"{word}:*"))
                )
            )
        ).scalar_one()
        if 0 < df <= total * _RARE_DF_CAP:
            ranked.append((df, word))
    ranked.sort()
    return [w for _, w in ranked[:_RARE_MAX_WORDS]]


def _rrf_fuse(rankings: list[list], limit: int, k: int = 60, max_judgments: int | None = None):
    """Reciprocal Rank Fusion: score(chunk) = Σ 1/(k + rank_i) over the
    rankings the chunk appears in (standard k=60). Judgments are capped at
    `max_judgments` of the final slots so statutes stay the primary ground."""
    scores: dict = {}
    keep: dict = {}
    for ranking in rankings:
        for rank, (chunk, doc) in enumerate(ranking, start=1):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)
            keep[chunk.id] = (chunk, doc)
    ordered = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    out: list = []
    judgments = 0
    for cid in ordered:
        chunk, doc = keep[cid]
        if max_judgments is not None and doc.doc_type == "judgment":
            if judgments >= max_judgments:
                continue
            judgments += 1
        out.append((chunk, doc))
        if len(out) >= limit:
            break
    return out


async def search_matter_documents(
    db: AsyncSession, matter_id: uuid.UUID, query: str, limit: int = 6
) -> list[dict]:
    """Hybrid search over a matter's documents (same recipe as the corpus,
    D-042): dense cosine + a full-text leg over the 'simple' config, fused
    with Reciprocal Rank Fusion. No judgment cap — these are case files."""
    base = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.matter_id == matter_id, Document.is_latest.is_(True))
    )
    fetch_n = max(limit * 4, 12)
    vec_rows: list = []
    vectors = embed([query])
    if vectors:
        stmt = (
            base.where(DocumentChunk.embedding.isnot(None))
            .order_by(DocumentChunk.embedding.cosine_distance(vectors[0]))
            .limit(fetch_n)
        )
        vec_rows = (await db.execute(stmt)).all()

    ts_query = func.plainto_tsquery("simple", query)
    fts_stmt = (
        base.where(DocumentChunk.tsv.isnot(None), DocumentChunk.tsv.op("@@")(ts_query))
        .order_by(func.ts_rank(DocumentChunk.tsv, ts_query).desc())
        .limit(fetch_n)
    )
    fts_rows = (await db.execute(fts_stmt)).all()

    if vec_rows or fts_rows:
        rows = _rrf_fuse([vec_rows, fts_rows], limit)
    else:
        rows = _score_rows((await db.execute(base.limit(2000))).all(), query, limit)

    return [
        {"text": chunk.text, "doc_title": doc.filename, "document_id": str(doc.id)}
        for chunk, doc in rows
    ]
