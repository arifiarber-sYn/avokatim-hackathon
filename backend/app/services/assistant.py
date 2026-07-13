"""Ava — the AI assistant. Every function builds a grounded prompt (matter
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
    "Ti je Ava, asistente juridike profesionale në aplikacionin AvokatIM. "
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


async def _build_ask_messages(
    db: AsyncSession,
    *,
    question: str,
    matter_id: uuid.UUID | None,
    jurisdiction_id: uuid.UUID | None,
    history: list[ChatMessage] | None = None,
    retrieval_query: str | None = None,
) -> tuple[list[ChatMessage], list[dict]]:
    """Shared RAG prompt assembly for ask_bora and ask_bora_stream."""
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
    return messages, citations


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
    messages, citations = await _build_ask_messages(
        db,
        question=question,
        matter_id=matter_id,
        jurisdiction_id=jurisdiction_id,
        history=history,
        retrieval_query=retrieval_query,
    )
    provider = get_provider(provider_name)
    result = await provider.chat(messages)
    return result.content, citations


async def ask_bora_stream(
    db: AsyncSession,
    *,
    question: str,
    matter_id: uuid.UUID | None,
    jurisdiction_id: uuid.UUID | None,
    provider_name: str | None = None,
    history: list[ChatMessage] | None = None,
):
    """Streaming variant: returns (citations, chunk_iterator). Chunks are
    ("thinking"|"delta", text) — thinking tokens are shown live but not saved."""
    messages, citations = await _build_ask_messages(
        db,
        question=question,
        matter_id=matter_id,
        jurisdiction_id=jurisdiction_id,
        history=history,
    )
    provider = get_provider(provider_name)
    return citations, provider.chat_stream(messages)


SUBQUESTIONS_PROMPT = """Po përgatitim një hulumtim të thelluar juridik për pyetjen e avokatit.
Zbërthe pyetjen në 3 deri 5 nën-pyetje kërkimi konkrete dhe të pavarura, të tilla që
secila të gjejë dispozita ligjore relevante në korpusin e ligjeve të Kosovës
(p.sh. baza ligjore, afatet, procedura, përjashtimet, praktika).
Kthe VETËM JSON të vlefshëm: një listë stringjesh në gjuhën e pyetjes, pa asgjë tjetër.

PYETJA E AVOKATIT:
{question}"""

DEEP_SYNTHESIS_INSTRUCTIONS = (
    "Kjo është përgjigja e një HULUMTIMI TË THELLUAR: materialet më lart janë "
    "mbledhur duke kërkuar çdo nën-pyetje veçmas në korpusin ligjor. Sintetizo "
    "një analizë të plotë e të strukturuar: (1) përgjigja e drejtpërdrejtë, "
    "(2) baza ligjore me citime të sakta (ligji + neni), (3) afatet dhe "
    "procedura nëse janë relevante, (4) rreziqet/përjashtimet, (5) hapat "
    "praktikë për avokatin. Cito vetëm nga materialet e dhëna."
)


def _extract_json_list(text: str) -> list | None:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else None
    except json.JSONDecodeError:
        return None


async def deep_research_stream(
    db: AsyncSession,
    *,
    question: str,
    matter_id: uuid.UUID | None,
    jurisdiction_id: uuid.UUID | None,
    provider_name: str | None = None,
):
    """CoCounsel-style deep research: decompose the question into sub-questions,
    search the corpus for each one, then synthesize a cited answer.
    Async generator of event dicts: step / thinking / delta / citations."""
    provider = get_provider(provider_name)

    yield {"type": "step", "step": "subquestions", "status": "start"}
    subquestions = [question]
    try:
        result = await provider.chat(
            [
                ChatMessage(role="system", content=SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=SUBQUESTIONS_PROMPT.format(question=question[:4000]),
                ),
            ]
        )
        parsed = _extract_json_list(result.content)
        if parsed:
            subquestions = [str(s).strip() for s in parsed if str(s).strip()][:5]
    except RuntimeError:
        pass  # fall back to researching the original question directly
    yield {
        "type": "step", "step": "subquestions", "status": "done",
        "subquestions": subquestions,
    }

    context_blocks: list[str] = []
    citations: list[dict] = []
    seen: set[tuple] = set()

    if matter_id:
        context_blocks.append(await build_matter_context(db, matter_id))
        for hit in await rag.search_matter_documents(db, matter_id, question, limit=6):
            context_blocks.append(f"[Nga dokumenti '{hit['doc_title']}']\n{hit['text']}")
            citations.append({"type": "document", "title": hit["doc_title"]})

    for index, subq in enumerate(subquestions, start=1):
        yield {
            "type": "step", "step": "search", "index": index,
            "total": len(subquestions), "question": subq,
        }
        if not jurisdiction_id:
            continue
        for hit in await rag.search_corpus(db, jurisdiction_id, subq, limit=4):
            key = (hit["doc_title"], hit["section"])
            if key in seen:
                continue
            seen.add(key)
            label = hit["doc_title"] + (f", {hit['section']}" if hit["section"] else "")
            context_blocks.append(f"[Nga ligji: {label}]\n{hit['text']}")
            citations.append(
                {"type": "law", "title": hit["doc_title"], "section": hit["section"],
                 "reference": hit["reference"]}
            )

    yield {"type": "step", "step": "synthesis", "status": "start"}
    user_content = question
    if context_blocks:
        user_content = (
            "MATERIALET E HULUMTIMIT (mbledhur për "
            + f"{len(subquestions)} nën-pyetje):\n\n"
            + "\n\n---\n\n".join(context_blocks)
            + f"\n\n=== PYETJA E AVOKATIT ===\n{question}"
            + f"\n\n{DEEP_SYNTHESIS_INSTRUCTIONS}"
        )
    messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_content),
    ]
    yield {"type": "citations", "citations": citations}
    async for kind, text in provider.chat_stream(messages):
        yield {"type": kind if kind == "thinking" else "delta", "text": text}


AI_ASSIST_PROMPT = """Je duke ndihmuar një avokat të përmirësojë draftin e një shkrese/kontrate.

UDHËZIMI I AVOKATIT:
{instruction}

Kthe VETËM JSON të vlefshëm me këto fusha:
- improved_text: teksti i plotë i përmirësuar (i njëjti dokument, jo pjesë), në gjuhën e draftit
- risk_flags: listë me maksimum 5 rreziqe juridike që vëren në draft (stringje të shkurtra në shqip, p.sh. "Mungon klauzola e juridiksionit"), [] nëse s'ka
- changes: listë me maksimum 5 stringje që përmbledhin çfarë ndryshove

Rregulla: mos shto fakte të reja, mos i ndrysho emrat/shifrat/datat ekzistuese,
ruaj vendet bosh __________ siç janë. Mos shto shpjegime jashtë JSON-it.

DRAFTI:
{draft}"""


async def ai_assist_template(
    draft: str, instruction: str, provider_name: str | None = None
) -> dict | None:
    """Improve a document draft per the lawyer's instruction; returns
    {improved_text, risk_flags, changes} or None if the LLM reply is unusable."""
    provider = get_provider(provider_name)
    result = await provider.chat(
        [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=AI_ASSIST_PROMPT.format(
                    instruction=instruction[:2000], draft=draft[:24000]
                ),
            ),
        ]
    )
    parsed = _extract_json(result.content)
    if not parsed or not parsed.get("improved_text"):
        return None
    return {
        "improved_text": str(parsed["improved_text"]),
        "risk_flags": [str(f) for f in parsed.get("risk_flags") or []][:5],
        "changes": [str(c) for c in parsed.get("changes") or []][:5],
    }


EXTRACT_DEADLINES_PROMPT = """Analizo këtë dokument gjyqësor dhe nxirr TË GJITHA datat
dhe afatet procedurale që përmban ose që rrjedhin prej tij.

Kthe VETËM JSON të vlefshëm — një listë objektesh me këto fusha:
- title: emërtim i shkurtër i afatit/ngjarjes në shqip (p.sh. "Afati i ankesës", "Seanca kryesore")
- kind: një nga [deadline, hearing, meeting]
- date: data në format YYYY-MM-DD (nëse dokumenti e cek direkt), ose null
- trigger_date: data e ngjarjes nga e cila rrjedh afati (p.sh. data e pranimit të vendimit), format YYYY-MM-DD, ose null
- days: numri i ditëve të afatit nëse përmendet (p.sh. 15 për ankesë), ose null
- legal_basis: baza ligjore nëse përmendet ose dihet (p.sh. "LPK neni 176"), ose null
- confidence: një nga [high, medium, low]

Rregulla:
- Përfshi edhe afatet e nënkuptuara nga lloji i dokumentit (p.sh. vendim i shkallës së parë → afati i ankesës).
- Mos shpik data. Nëse data s'është e qartë, vendos null dhe confidence "low".
- Maksimum 10 rezultate, vetëm çka është relevante procedurale.

DOKUMENTI:
{text}"""


async def extract_deadlines_from_text(
    text: str, provider_name: str | None = None
) -> list[dict]:
    """Ask the LLM to extract procedural dates/deadlines from a court document."""
    provider = get_provider(provider_name)
    result = await provider.chat(
        [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user", content=EXTRACT_DEADLINES_PROMPT.format(text=text[:24000])
            ),
        ]
    )
    match = re.search(r"\[.*\]", result.content, re.DOTALL)
    if not match:
        single = _extract_json(result.content)
        return [single] if single else []
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


SUMMARIZE_DOC_PROMPT = """Përmblidh këtë dokument juridik për avokatin.
Kthe VETËM JSON të vlefshëm me këto fusha:
- summary: përmbledhje 3-5 fjalish në shqip (çfarë është dokumenti, palët, thelbi)
- key_points: listë me maksimum 6 pika kyçe (stringje të shkurtra)

DOKUMENTI:
{text}"""


async def summarize_document_text(
    text: str, provider_name: str | None = None
) -> dict | None:
    """Summarize an extracted document text; returns {summary, key_points,
    deadlines} (deadlines via the existing extractor) or None if unusable."""
    provider = get_provider(provider_name)
    result = await provider.chat(
        [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user", content=SUMMARIZE_DOC_PROMPT.format(text=text[:24000])
            ),
        ]
    )
    parsed = _extract_json(result.content)
    if not parsed or not parsed.get("summary"):
        return None
    deadlines = await extract_deadlines_from_text(text, provider_name)
    return {
        "summary": str(parsed["summary"]),
        "key_points": [str(p) for p in parsed.get("key_points") or []][:6],
        "deadlines": deadlines[:10],
    }


CLIENT_UPDATE_PROMPT = """Drafto një njoftim të shkurtër profesional për klientin e kësaj
lënde, në emër të avokatit. Njoftimi duhet:
- të shkruhet në gjuhën shqipe, me ton të ngrohtë por profesional
- të përmbledhë ku ndodhet lënda aktualisht (pa zhargon të tepërt juridik)
- të tregojë hapat e radhës dhe afatet/seancat e ardhshme nëse ka
- të mos premtojë rezultate dhe të mos japë këshilla të reja ligjore
- maksimum 200 fjalë, pa hyrje "Shpresoj se..." të tepërta

Kthe vetëm tekstin e njoftimit, pa shpjegime shtesë."""


async def draft_client_update(
    db: AsyncSession,
    *,
    matter_id: uuid.UUID,
    extra_instructions: str | None = None,
    provider_name: str | None = None,
) -> str:
    context = await build_matter_context(db, matter_id)
    question = CLIENT_UPDATE_PROMPT
    if extra_instructions:
        question += f"\n\nUdhëzime shtesë nga avokati: {extra_instructions}"
    provider = get_provider(provider_name)
    result = await provider.chat(
        [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=f"{context}\n\n=== DETYRA ===\n{question}"),
        ]
    )
    return result.content


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
