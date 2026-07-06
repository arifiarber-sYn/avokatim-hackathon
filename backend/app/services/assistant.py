"""Bora — the AI assistant. Every function builds a grounded prompt (matter
facts, documents, legal corpus citations) and calls the selected LLM provider."""
import json
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm import get_provider
from app.llm.base import ChatMessage
from app.models import Deadline, Document, Matter, MatterNote, MatterParty
from app.services import rag

SYSTEM_PROMPT = (
    "Ti je Bora, asistente juridike profesionale në aplikacionin BoraLaw. "
    "Punon për një avokat të licencuar. Përgjigju në gjuhën e pyetjes "
    "(shqip, anglisht ose kinezisht). Bazohu VETËM në materialet e dhëna "
    "dhe në parimet e përgjithshme juridike; kur citon ligj, shëno saktë "
    "burimin (p.sh. 'LPK neni 176'). Kur nuk je e sigurt, thuaje hapur. "
    "Përgjigjet e tua janë ndihmë profesionale për avokatin — vendimi "
    "përfundimtar është gjithmonë i avokatit."
)

CLASSIFY_PROMPT = """Klasifiko këtë përshkrim të një rasti të ri ligjor.
Kthe VETËM JSON të vlefshëm me këto fusha:
- practice_area: një nga [civil, criminal, family, commercial, labor, administrative, other]
- suggested_title: titull i shkurtër i lëndës në shqip (maks 80 karaktere)
- urgency: një nga [low, medium, high] (high nëse ka afate të afërta ose paraburgim)
- key_issues: listë me maksimum 4 çështje kryesore juridike
- summary: përmbledhje 2-fjalishe

Përshkrimi:
{summary}"""


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


async def classify_intake(summary: str, provider_name: str | None = None) -> dict | None:
    provider = get_provider(provider_name)
    result = await provider.chat(
        [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=CLASSIFY_PROMPT.format(summary=summary[:6000])),
        ]
    )
    return _extract_json(result.content)


async def build_matter_context(db: AsyncSession, matter_id: uuid.UUID) -> str:
    """Assemble the matter file into a compact text context for the LLM."""
    matter = (
        await db.execute(
            select(Matter)
            .options(selectinload(Matter.client))
            .where(Matter.id == matter_id)
        )
    ).scalar_one()

    parts = [
        f"LËNDA {matter.reference}: {matter.title}",
        f"Fusha: {matter.practice_area} | Statusi: {matter.status}",
    ]
    if matter.client:
        parts.append(f"Klienti: {matter.client.display_name}")
    if matter.court_name:
        parts.append(f"Gjykata: {matter.court_name} ({matter.court_case_number or 'pa numër'})")
    if matter.description:
        parts.append(f"Përshkrimi: {matter.description[:3000]}")

    parties = (
        await db.execute(
            select(MatterParty)
            .options(selectinload(MatterParty.contact))
            .where(MatterParty.matter_id == matter_id)
        )
    ).scalars().all()
    if parties:
        parts.append(
            "Palët: "
            + "; ".join(f"{p.contact.display_name} ({p.role})" for p in parties)
        )

    deadlines = (
        await db.execute(
            select(Deadline)
            .where(Deadline.matter_id == matter_id, Deadline.status == "pending")
            .order_by(Deadline.due_at)
        )
    ).scalars().all()
    if deadlines:
        parts.append(
            "Afatet aktive: "
            + "; ".join(f"{d.title} deri më {d.due_at:%d.%m.%Y}" for d in deadlines)
        )

    notes = (
        await db.execute(
            select(MatterNote)
            .where(MatterNote.matter_id == matter_id)
            .order_by(MatterNote.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    for n in notes:
        parts.append(f"Shënim ({n.created_at:%d.%m.%Y}): {n.body[:500]}")

    docs = (
        await db.execute(
            select(Document).where(
                Document.matter_id == matter_id, Document.is_latest.is_(True)
            )
        )
    ).scalars().all()
    if docs:
        parts.append("Dokumentet: " + "; ".join(d.filename for d in docs))

    return "\n".join(parts)


async def ask_bora(
    db: AsyncSession,
    *,
    question: str,
    matter_id: uuid.UUID | None,
    jurisdiction_id: uuid.UUID | None,
    provider_name: str | None = None,
    history: list[ChatMessage] | None = None,
    retrieval_query: str | None = None,
) -> tuple[str, list[dict]]:
    """RAG-grounded chat. Returns (answer, citations). retrieval_query lets
    callers search with case facts instead of a generic instruction prompt."""
    context_blocks: list[str] = []
    citations: list[dict] = []
    search_text = retrieval_query or question

    if matter_id:
        context_blocks.append(await build_matter_context(db, matter_id))
        doc_hits = await rag.search_matter_documents(db, matter_id, search_text, limit=10)
        for hit in doc_hits:
            context_blocks.append(f"[Nga dokumenti '{hit['doc_title']}']\n{hit['text']}")
            citations.append({"type": "document", "title": hit["doc_title"]})

    if jurisdiction_id:
        law_hits = await rag.search_corpus(db, jurisdiction_id, search_text)
        for hit in law_hits:
            label = f"{hit['doc_title']}" + (f", {hit['section']}" if hit["section"] else "")
            context_blocks.append(f"[Nga ligji: {label}]\n{hit['text']}")
            citations.append(
                {"type": "law", "title": hit["doc_title"], "section": hit["section"],
                 "reference": hit["reference"]}
            )

    user_content = question
    if context_blocks:
        user_content = (
            "MATERIALET E LËNDËS DHE BAZA LIGJORE:\n\n"
            + "\n\n---\n\n".join(context_blocks)
            + f"\n\n=== PYETJA E AVOKATIT ===\n{question}"
        )

    messages = [ChatMessage(role="system", content=SYSTEM_PROMPT)]
    if history:
        messages.extend(history[-8:])
    messages.append(ChatMessage(role="user", content=user_content))

    provider = get_provider(provider_name)
    result = await provider.chat(messages)
    return result.content, citations


HEARING_PREP_PROMPT = """Përgatit avokatin për seancën gjyqësore të kësaj lënde.
Struktura e përgjigjes:
1. KRONOLOGJIA E FAKTEVE — faktet kyçe në rend kohor
2. ÇËSHTJET JURIDIKE — çështjet që do të diskutohen, me bazën ligjore
3. ARGUMENTET TONA — pikat më të forta, me mbështetjen në prova
4. DOBËSITË DHE KUNDËRARGUMENTET — çka pritet nga pala tjetër dhe si përgjigjemi
5. PYETJE PËR DËSHMITARËT — nëse ka dëshmitarë, pyetjet e sugjeruara
6. LISTA E KONTROLLIT — dokumentet dhe provat për të marrë me vete"""


async def hearing_prep(
    db: AsyncSession,
    *,
    matter_id: uuid.UUID,
    jurisdiction_id: uuid.UUID | None,
    extra_instructions: str | None = None,
    provider_name: str | None = None,
) -> tuple[str, list[dict]]:
    question = HEARING_PREP_PROMPT
    if extra_instructions:
        question += f"\n\nUdhëzime shtesë nga avokati: {extra_instructions}"

    matter = await db.get(Matter, matter_id)
    retrieval_query = f"{matter.title} {matter.description or ''}"[:1000]

    return await ask_bora(
        db,
        question=question,
        matter_id=matter_id,
        jurisdiction_id=jurisdiction_id,
        provider_name=provider_name,
        retrieval_query=retrieval_query,
    )
