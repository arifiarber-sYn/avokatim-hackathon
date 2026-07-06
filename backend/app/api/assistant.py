import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.llm import list_providers
from app.llm.base import ChatMessage
from app.models import Conversation, Message, User
from app.schemas.assistant import (
    AskRequest,
    AskResponse,
    ConversationOut,
    HearingPrepRequest,
    MessageOut,
    SummarizeResponse,
)
from app.services.assistant import ask_bora, hearing_prep
from app.services.audit import log_action

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/providers")
async def providers(user: User = Depends(get_current_user)):
    """Available LLM backends — the lawyer picks external (DeepSeek) or local."""
    return list_providers()


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


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    jurisdiction_id = None
    if body.matter_id:
        matter = await get_owned_matter(db, user, body.matter_id)
        jurisdiction_id = matter.jurisdiction_id

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

    try:
        answer, citations = await ask_bora(
            db,
            question=body.question,
            matter_id=body.matter_id or conversation.matter_id,
            jurisdiction_id=jurisdiction_id,
            provider_name=body.provider,
            history=history,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

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
    return AskResponse(conversation_id=conversation.id, message=reply)


@router.post("/matters/{matter_id}/summarize", response_model=SummarizeResponse)
async def summarize_matter(
    matter_id: uuid.UUID,
    provider: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    matter = await get_owned_matter(db, user, matter_id)
    try:
        answer, citations = await ask_bora(
            db,
            question=(
                "Bëj një përmbledhje profesionale të kësaj lënde: gjendja aktuale, "
                "faktet kyçe, hapat e ardhshëm të rekomanduar dhe rreziqet."
            ),
            matter_id=matter_id,
            jurisdiction_id=matter.jurisdiction_id,
            provider_name=provider,
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
    try:
        answer, citations = await hearing_prep(
            db,
            matter_id=body.matter_id,
            jurisdiction_id=matter.jurisdiction_id,
            extra_instructions=body.extra_instructions,
            provider_name=body.provider,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="assistant.hearing_prep",
        entity_type="matter", entity_id=str(body.matter_id),
    )
    await db.commit()
    return SummarizeResponse(summary=answer, citations=citations)
