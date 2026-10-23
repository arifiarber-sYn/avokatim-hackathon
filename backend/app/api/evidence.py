"""Evidence vault endpoints (D-018).

Citizen side (/public/citizen/evidence): start a session, stream chunks
while recording, finish (triggers local transcription), list, download the
audio and the chain-of-custody PDF. Lawyer side (/marketplace/cases/...):
read-only access to the evidence attached to a case their tenant claimed.
"""
import logging
import uuid
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.marketplace import _current_citizen, _ip, _owned_case, _rate_limit, _tenant_case
from app.database import get_db
from app.deps import get_current_user
from app.models import CitizenUser, EvidenceChunk, EvidenceSession, User
from app.services import evidence
from app.services.audit import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/citizen/evidence", tags=["evidence"])
lawyer_router = APIRouter(prefix="/marketplace/cases", tags=["evidence"])

EVIDENCE_KINDS = ("sos_audio", "sos_video", "call")
ALLOWED_MIMES = ("audio/webm", "video/webm", "audio/mp4", "video/mp4", "audio/ogg")


class StartIn(BaseModel):
    kind: str = "sos_audio"
    mime: str = "audio/webm"
    case_request_id: uuid.UUID | None = None
    consent: bool = False


@router.post("/start", status_code=201)
async def start_session(
    body: StartIn,
    request: Request,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    await _rate_limit("evidence_start", str(citizen.id), limit=20, window_seconds=24 * 3600)
    if body.kind not in EVIDENCE_KINDS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown kind")
    if body.mime.split(";")[0].strip() not in ALLOWED_MIMES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported mime")
    if not body.consent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Consent required")
    if body.case_request_id is not None:
        await _owned_case(db, citizen, body.case_request_id)

    session = EvidenceSession(
        citizen_id=citizen.id,
        case_request_id=body.case_request_id,
        kind=body.kind,
        mime=body.mime.split(";")[0].strip(),
        locale=citizen.locale,
        consent_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()
    await log_action(
        db, tenant_id=None, user_id=None, action="evidence.start",
        entity_type="evidence_session", entity_id=str(session.id),
        details={"kind": body.kind}, ip_address=_ip(request),
    )
    await db.commit()
    return evidence.session_out(session)


async def _owned_session(
    db: AsyncSession, citizen: CitizenUser, session_id: uuid.UUID
) -> EvidenceSession:
    session = await db.get(EvidenceSession, session_id)
    if session is None or session.citizen_id != citizen.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return session


@router.post("/{session_id}/chunks", status_code=201)
async def upload_chunk(
    session_id: uuid.UUID,
    seq: int = Form(ge=0, le=evidence.MAX_SESSION_CHUNKS - 1),
    chunk: UploadFile = File(...),
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    session = await _owned_session(db, citizen, session_id)
    if session.status != "recording":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Session already finished")
    if seq != session.chunk_count:
        # Strict ordering keeps the chain meaningful; the client retries in order
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Expected seq {session.chunk_count}"
        )
    data = await chunk.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty chunk")
    if len(data) > evidence.MAX_CHUNK_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Chunk too large")
    if session.total_bytes + len(data) > evidence.MAX_SESSION_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Session too large")

    row = evidence.store_chunk(session, seq, data)
    db.add(row)
    await db.commit()
    return {"seq": row.seq, "sha256": row.sha256, "chain_hash": row.chain_hash}


class FinishIn(BaseModel):
    case_request_id: uuid.UUID | None = None


@router.post("/{session_id}/finish")
async def finish_session(
    session_id: uuid.UUID,
    body: FinishIn,
    request: Request,
    background: BackgroundTasks,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    session = await _owned_session(db, citizen, session_id)
    if session.status == "finished":
        return evidence.session_out(session)
    session.status = "finished"
    session.finished_at = datetime.now(UTC)
    session.transcript_status = "pending"
    # Late attach: the SOS case is usually created while already recording
    if body.case_request_id is not None and session.case_request_id is None:
        await _owned_case(db, citizen, body.case_request_id)
        session.case_request_id = body.case_request_id
    await log_action(
        db, tenant_id=None, user_id=None, action="evidence.finish",
        entity_type="evidence_session", entity_id=str(session.id),
        details={"chunks": session.chunk_count, "bytes": session.total_bytes},
        ip_address=_ip(request),
    )
    await db.commit()
    background.add_task(evidence.transcribe_session, session.id)
    return evidence.session_out(session)


@router.get("")
async def list_sessions(
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(EvidenceSession)
            .where(EvidenceSession.citizen_id == citizen.id)
            .order_by(EvidenceSession.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    return [evidence.session_out(s) for s in rows]


async def _session_chunks(db: AsyncSession, session_id: uuid.UUID) -> list[EvidenceChunk]:
    return list(
        (
            await db.execute(
                select(EvidenceChunk)
                .where(EvidenceChunk.session_id == session_id)
                .order_by(EvidenceChunk.seq)
            )
        ).scalars().all()
    )


def _audio_response(session: EvidenceSession, data: bytes) -> Response:
    ext = "webm" if "webm" in session.mime else "mp4"
    return Response(
        content=data,
        media_type=session.mime,
        headers={
            "Content-Disposition": f'attachment; filename="deshmia-{session.id}.{ext}"',
            "Cache-Control": "no-store",
        },
    )


def _package_response(session: EvidenceSession, pdf: bytes) -> Response:
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="pako-deshmie-{session.id}.pdf"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/{session_id}/audio")
async def download_audio(
    session_id: uuid.UUID,
    request: Request,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    session = await _owned_session(db, citizen, session_id)
    chunks = await _session_chunks(db, session_id)
    if not chunks:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No recorded data")
    await log_action(
        db, tenant_id=None, user_id=None, action="evidence.download",
        entity_type="evidence_session", entity_id=str(session.id),
        details={"side": "citizen"}, ip_address=_ip(request),
    )
    await db.commit()
    return _audio_response(session, evidence.load_audio(session, chunks))


@router.get("/{session_id}/package")
async def download_package(
    session_id: uuid.UUID,
    request: Request,
    citizen: CitizenUser = Depends(_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    session = await _owned_session(db, citizen, session_id)
    chunks = await _session_chunks(db, session_id)
    pdf = evidence.build_package_pdf(session, chunks, citizen.full_name)
    await log_action(
        db, tenant_id=None, user_id=None, action="evidence.package",
        entity_type="evidence_session", entity_id=str(session.id),
        details={"side": "citizen"}, ip_address=_ip(request),
    )
    await db.commit()
    return _package_response(session, pdf)


# ---------- lawyer side: evidence attached to a claimed case ----------

@lawyer_router.get("/{case_id}/evidence")
async def case_evidence(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _tenant_case(db, user, case_id)
    rows = (
        await db.execute(
            select(EvidenceSession)
            .where(EvidenceSession.case_request_id == case_id)
            .order_by(EvidenceSession.created_at)
        )
    ).scalars().all()
    return [evidence.session_out(s) for s in rows]


async def _case_session(
    db: AsyncSession, user: User, case_id: uuid.UUID, session_id: uuid.UUID
) -> EvidenceSession:
    await _tenant_case(db, user, case_id)
    session = await db.get(EvidenceSession, session_id)
    if session is None or session.case_request_id != case_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return session


@lawyer_router.get("/{case_id}/evidence/{session_id}/audio")
async def lawyer_download_audio(
    case_id: uuid.UUID,
    session_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _case_session(db, user, case_id, session_id)
    chunks = await _session_chunks(db, session_id)
    if not chunks:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No recorded data")
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="evidence.download",
        entity_type="evidence_session", entity_id=str(session.id),
        details={"side": "lawyer"}, ip_address=_ip(request),
    )
    await db.commit()
    return _audio_response(session, evidence.load_audio(session, chunks))


@lawyer_router.get("/{case_id}/evidence/{session_id}/package")
async def lawyer_download_package(
    case_id: uuid.UUID,
    session_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _case_session(db, user, case_id, session_id)
    chunks = await _session_chunks(db, session_id)
    citizen = await db.get(CitizenUser, session.citizen_id)
    pdf = evidence.build_package_pdf(
        session, chunks, citizen.full_name if citizen else "?"
    )
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="evidence.package",
        entity_type="evidence_session", entity_id=str(session.id),
        details={"side": "lawyer"}, ip_address=_ip(request),
    )
    await db.commit()
    return _package_response(session, pdf)
