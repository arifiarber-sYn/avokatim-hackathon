import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.matters import get_owned_matter
from app.database import SessionLocal, get_db
from app.deps import get_current_user
from app.llm import list_providers
from app.llm.base import ChatMessage
from app.models import Conversation, Jurisdiction, Message, Tenant, User
from app.schemas.assistant import (
    AskRequest,
    AskResponse,
    ConversationOut,
    HearingPrepRequest,
    MessageOut,
    SummarizeResponse,
)
from app.services.assistant import (
    ask_bora,
    ask_bora_stream,
    deep_research_stream,
    hearing_prep,
    prepare_matter_stream,
)
from app.services.audit import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["assistant"])


async def _external_ai_allowed(db: AsyncSession, user: User) -> bool:
    """Tenant switch for international data transfers (Law 06/L-082 art. 49):
    when off, the assistant is forced to the local provider."""
    tenant = await db.get(Tenant, user.tenant_id)
    return bool(tenant.allow_external_ai) if tenant else True


async def _effective_provider(
    db: AsyncSession, user: User, requested: str | None
) -> str | None:
    if not await _external_ai_allowed(db, user):
        return "local"
    return requested


async def _office_style(db: AsyncSession, user: User) -> str | None:
    tenant = await db.get(Tenant, user.tenant_id)
    return tenant.assistant_style if tenant else None


@router.post("/export-docx")
async def export_docx(
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export any assistant output (e.g. the prepare-matter draft) as a styled
    Word document — lawyers finish their drafting in Word."""
    from fastapi.responses import Response

    from app.services.docx_render import build_docx

    content = str(body.get("content") or "").strip()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "content is required")
    title = str(body.get("title") or "Draft")[:120]
    docx_bytes = build_docx(content[:100_000], title=title)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="assistant.export_docx",
        entity_type="assistant", entity_id="", details={"title": title},
    )
    await db.commit()
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{title}.docx"'},
    )


@router.get("/style")
async def get_style(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Office memory: standing preferences Ava applies on every request."""
    return {"style": await _office_style(db, user)}


@router.put("/style")
async def set_style(
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, user.tenant_id)
    style = str(body.get("style") or "").strip()[:2000]
    tenant.assistant_style = style or None
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="assistant.style",
        entity_type="tenant", entity_id=str(tenant.id), details={},
    )
    await db.commit()
    return {"style": tenant.assistant_style}


class OfficeAskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    language: str = "sq"
    provider: str | None = None


@router.post("/office-ask")
async def office_ask_endpoint(
    body: OfficeAskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Office-level Ava: firm-data questions answered through a fixed pipeline
    of ~8 predefined, tenant-scoped queries (D-030: no free-form tool loop)."""
    from app.services.office_ask import office_ask

    provider_name = await _effective_provider(db, user, body.provider)
    try:
        result = await office_ask(
            db,
            tenant_id=user.tenant_id,
            question=body.question,
            language=body.language,
            provider_name=provider_name,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="assistant.office_ask",
        entity_type="assistant", entity_id="", details={"tool": result["tool"]},
    )
    await db.commit()
    return result


@router.get("/providers")
async def providers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Available LLM backends — the lawyer picks external (DeepSeek) or local.
    Includes the tenant's external-AI switch so the UI can warn/gate."""
    return {
        "providers": list_providers(),
        "external_ai_allowed": await _external_ai_allowed(db, user),
    }


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    matter_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Conversation).where(
        Conversation.tenant_id == user.tenant_id, Conversation.user_id == user.id
    )
    if matter_id:
        stmt = stmt.where(Conversation.matter_id == matter_id)
    stmt = stmt.order_by(Conversation.updated_at.desc()).limit(50)
    return (await db.execute(stmt)).scalars().all()


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def conversation_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None or conversation.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return (await db.execute(stmt)).scalars().all()


async def _prepare_ask(
    db: AsyncSession, user: User, body: AskRequest
) -> tuple[Conversation, list[ChatMessage], uuid.UUID | None]:
    """Resolve jurisdiction + conversation + history for an /ask request."""
    jurisdiction_id = None
    if body.matter_id:
        matter = await get_owned_matter(db, user, body.matter_id)
        jurisdiction_id = matter.jurisdiction_id
    else:
        # No matter given: still ground answers in the tenant's default
        # jurisdiction corpus so Ava cites the actual laws.
        tenant = await db.get(Tenant, user.tenant_id)
        code = tenant.default_jurisdiction_code if tenant else "XK"
        jurisdiction = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == code))
        ).scalar_one_or_none()
        if jurisdiction:
            jurisdiction_id = jurisdiction.id

    if body.conversation_id:
        conversation = (
            await db.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(Conversation.id == body.conversation_id)
            )
        ).scalar_one_or_none()
        if conversation is None or conversation.tenant_id != user.tenant_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
        history = [
            ChatMessage(role=m.role, content=m.content)
            for m in conversation.messages
            if m.role in ("user", "assistant")
        ]
    else:
        conversation = Conversation(
            tenant_id=user.tenant_id,
            user_id=user.id,
            matter_id=body.matter_id,
            title=body.question[:200],
            provider=body.provider or "deepseek",
        )
        db.add(conversation)
        await db.flush()
        history = []

    return conversation, history, jurisdiction_id


async def _save_exchange(
    db: AsyncSession,
    user: User,
    body: AskRequest,
    conversation: Conversation,
    answer: str,
    citations: list[dict],
) -> Message:
    db.add(Message(conversation_id=conversation.id, role="user", content=body.question))
    reply = Message(
        conversation_id=conversation.id, role="assistant", content=answer, citations=citations
    )
    db.add(reply)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="assistant.ask",
        entity_type="conversation", entity_id=str(conversation.id),
        details={"provider": body.provider or "deepseek"},
    )
    await db.commit()
    await db.refresh(reply)
    return reply


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation, history, jurisdiction_id = await _prepare_ask(db, user, body)
    provider_name = await _effective_provider(db, user, body.provider)

    try:
        answer, citations = await ask_bora(
            db,
            question=body.question,
            matter_id=body.matter_id or conversation.matter_id,
            jurisdiction_id=jurisdiction_id,
            provider_name=provider_name,
            history=history,
            language=body.locale,
            style=await _office_style(db, user),
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

    reply = await _save_exchange(db, user, body, conversation, answer, citations)
    return AskResponse(conversation_id=conversation.id, message=reply)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/ask-stream")
async def ask_stream(body: AskRequest, user: User = Depends(get_current_user)):
    """Streaming variant of /ask (Server-Sent Events). Keeps data flowing so
    no proxy/browser/tunnel idle timeout can kill long answers, and the
    lawyer sees the answer as it is written."""

    async def event_stream():
        # Own session: the request-scoped one may be torn down while the
        # response body is still streaming.
        async with SessionLocal() as db:
            try:
                conversation, history, jurisdiction_id = await _prepare_ask(db, user, body)
            except HTTPException as exc:
                yield _sse({"type": "error", "detail": exc.detail})
                return

            yield _sse({"type": "meta", "conversation_id": str(conversation.id)})

            provider_name = await _effective_provider(db, user, body.provider)
            parts: list[str] = []
            try:
                citations, chunks = await ask_bora_stream(
                    db,
                    question=body.question,
                    matter_id=body.matter_id or conversation.matter_id,
                    jurisdiction_id=jurisdiction_id,
                    provider_name=provider_name,
                    history=history,
                    language=body.locale,
                    style=await _office_style(db, user),
                )
                async for kind, text in chunks:
                    if kind == "thinking":
                        yield _sse({"type": "thinking", "text": text})
                    else:
                        parts.append(text)
                        yield _sse({"type": "delta", "text": text})
            except Exception as exc:
                logger.exception("ask-stream failed")
                await db.rollback()
                yield _sse({"type": "error", "detail": str(exc)})
                return

            reply = await _save_exchange(db, user, body, conversation, "".join(parts), citations)
            yield _sse(
                {
                    "type": "done",
                    "conversation_id": str(conversation.id),
                    "message": MessageOut.model_validate(reply).model_dump(mode="json"),
                }
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/deep-research")
async def deep_research(body: AskRequest, user: User = Depends(get_current_user)):
    """Deep research (SSE): sub-questions → per-question corpus search →
    synthesized answer with merged citations. Progress is streamed as
    'step' events so the lawyer sees what Ava is doing."""

    async def event_stream():
        async with SessionLocal() as db:
            try:
                conversation, _history, jurisdiction_id = await _prepare_ask(db, user, body)
            except HTTPException as exc:
                yield _sse({"type": "error", "detail": exc.detail})
                return

            yield _sse({"type": "meta", "conversation_id": str(conversation.id)})

            provider_name = await _effective_provider(db, user, body.provider)
            parts: list[str] = []
            citations: list[dict] = []
            try:
                events = deep_research_stream(
                    db,
                    question=body.question,
                    matter_id=body.matter_id or conversation.matter_id,
                    jurisdiction_id=jurisdiction_id,
                    provider_name=provider_name,
                    language=body.locale,
                )
                async for event in events:
                    if event["type"] == "citations":
                        citations = event["citations"]
                        continue
                    if event["type"] == "delta":
                        parts.append(event["text"])
                    yield _sse(event)
            except Exception as exc:
                logger.exception("deep-research failed")
                await db.rollback()
                yield _sse({"type": "error", "detail": str(exc)})
                return

            reply = await _save_exchange(
                db, user, body, conversation, "".join(parts), citations
            )
            yield _sse(
                {
                    "type": "done",
                    "conversation_id": str(conversation.id),
                    "message": MessageOut.model_validate(reply).model_dump(mode="json"),
                }
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/matters/{matter_id}/prepare")
async def prepare_matter(
    matter_id: uuid.UUID,
    provider: str | None = None,
    locale: str | None = None,
    user: User = Depends(get_current_user),
):
    """Agentic matter preparation (SSE): Ava reads the file, derives the legal
    questions, researches each in the corpus and returns situation + legal
    basis + next steps + a ready-to-edit draft, streaming progress live."""

    async def event_stream():
        async with SessionLocal() as db:
            try:
                matter = await get_owned_matter(db, user, matter_id)
            except HTTPException as exc:
                yield _sse({"type": "error", "detail": exc.detail})
                return
            provider_name = await _effective_provider(db, user, provider)
            try:
                events = prepare_matter_stream(
                    db,
                    matter_id=matter.id,
                    jurisdiction_id=matter.jurisdiction_id,
                    provider_name=provider_name,
                    language=locale,
                    style=await _office_style(db, user),
                )
                async for event in events:
                    yield _sse(event)
            except Exception as exc:
                logger.exception("prepare-matter failed")
                await db.rollback()
                yield _sse({"type": "error", "detail": str(exc)})
                return
            await log_action(
                db, tenant_id=user.tenant_id, user_id=user.id,
                action="assistant.prepare_matter", entity_type="matter",
                entity_id=str(matter.id), details={},
            )
            await db.commit()
            yield _sse({"type": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/matters/{matter_id}/summarize", response_model=SummarizeResponse)
async def summarize_matter(
    matter_id: uuid.UUID,
    provider: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    matter = await get_owned_matter(db, user, matter_id)
    provider_name = await _effective_provider(db, user, provider)
    try:
        answer, citations = await ask_bora(
            db,
            question=(
                "Bëj një përmbledhje profesionale të kësaj lënde: gjendja aktuale, "
                "faktet kyçe, hapat e ardhshëm të rekomanduar dhe rreziqet."
            ),
            matter_id=matter_id,
            jurisdiction_id=matter.jurisdiction_id,
            provider_name=provider_name,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    return SummarizeResponse(summary=answer, citations=citations)


@router.post("/hearing-prep", response_model=SummarizeResponse)
async def prep_for_hearing(
    body: HearingPrepRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Court-day preparation: chronology, arguments, weaknesses, witness
    questions and a checklist — grounded in the matter file."""
    matter = await get_owned_matter(db, user, body.matter_id)
    provider_name = await _effective_provider(db, user, body.provider)
    try:
        answer, citations = await hearing_prep(
            db,
            matter_id=body.matter_id,
            jurisdiction_id=matter.jurisdiction_id,
            extra_instructions=body.extra_instructions,
            provider_name=provider_name,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="assistant.hearing_prep",
        entity_type="matter", entity_id=str(body.matter_id),
    )
    await db.commit()
    return SummarizeResponse(summary=answer, citations=citations)
