"""Evidence vault service: encrypted chunk storage, hash chain, package PDF.

Chunks are stored encrypted (same Fernet key as documents) under
data/evidence/<session_id>/<seq>. WebM chunks produced by one MediaRecorder
concatenate back into a playable file, so streaming the decrypted chunks in
order reconstructs the original recording bit-for-bit.
"""
import hashlib
import logging
import uuid
from datetime import UTC, datetime
from html import escape
from pathlib import Path

from app.config import settings
from app.models import EvidenceChunk, EvidenceSession
from app.services.storage import _fernet

logger = logging.getLogger(__name__)

EVIDENCE_DIR = settings.documents_dir.parent / "evidence"

MAX_CHUNK_BYTES = 3 * 1024 * 1024        # MediaRecorder 5s slices are ~50-100 KB
MAX_SESSION_BYTES = 200 * 1024 * 1024    # ~3h of opus audio
MAX_SESSION_CHUNKS = 4000


def _chunk_path(session_id: uuid.UUID, seq: int) -> Path:
    return EVIDENCE_DIR / str(session_id) / f"{seq:06d}.bin"


def chain_hash(prev_chain: str | None, chunk_sha256: str) -> str:
    """H_n = sha256(H_{n-1} || sha256_n) — binds content AND order."""
    return hashlib.sha256(((prev_chain or "") + chunk_sha256).encode()).hexdigest()


def store_chunk(session: EvidenceSession, seq: int, data: bytes) -> EvidenceChunk:
    """Hash, chain, encrypt, write. Caller adds the returned row to the db."""
    sha = hashlib.sha256(data).hexdigest()
    new_chain = chain_hash(session.chain_hash, sha)
    fernet = _fernet()
    stored = fernet.encrypt(data) if fernet else data
    path = _chunk_path(session.id, seq)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stored)

    chunk = EvidenceChunk(
        session_id=session.id,
        seq=seq,
        size_bytes=len(data),
        sha256=sha,
        prev_hash=session.chain_hash,
        chain_hash=new_chain,
    )
    session.chain_hash = new_chain
    session.chunk_count = seq + 1
    session.total_bytes = (session.total_bytes or 0) + len(data)
    return chunk


def load_audio(session: EvidenceSession, chunks: list[EvidenceChunk]) -> bytes:
    fernet = _fernet()
    parts: list[bytes] = []
    for chunk in sorted(chunks, key=lambda c: c.seq):
        raw = _chunk_path(session.id, chunk.seq).read_bytes()
        parts.append(fernet.decrypt(raw) if fernet else raw)
    return b"".join(parts)


def verify_chain(chunks: list[EvidenceChunk]) -> bool:
    prev: str | None = None
    for chunk in sorted(chunks, key=lambda c: c.seq):
        if chunk.prev_hash != prev or chunk.chain_hash != chain_hash(prev, chunk.sha256):
            return False
        prev = chunk.chain_hash
    return True


async def transcribe_session(session_id: uuid.UUID) -> None:
    """Background: reconstruct the audio and transcribe it locally."""
    from app.database import SessionLocal
    from app.services import voice
    from sqlalchemy import select

    if not voice.stt_enabled():
        return
    async with SessionLocal() as db:
        session = await db.get(EvidenceSession, session_id)
        if session is None:
            return
        chunks = (
            await db.execute(
                select(EvidenceChunk).where(EvidenceChunk.session_id == session_id)
            )
        ).scalars().all()
        if not chunks:
            session.transcript_status = "empty"
            await db.commit()
            return
        try:
            audio = load_audio(session, list(chunks))
            result = await voice.transcribe(audio, language=session.locale)
            session.transcript = result["text"] or None
            session.transcript_status = "done"
        except Exception:
            logger.exception("Evidence transcription failed for %s", session_id)
            session.transcript_status = "failed"
        await db.commit()


def session_out(session: EvidenceSession) -> dict:
    return {
        "id": str(session.id),
        "case_request_id": str(session.case_request_id) if session.case_request_id else None,
        "kind": session.kind,
        "mime": session.mime,
        "status": session.status,
        "started_at": session.created_at.isoformat(),
        "finished_at": session.finished_at.isoformat() if session.finished_at else None,
        "chunk_count": session.chunk_count,
        "total_bytes": session.total_bytes,
        "chain_hash": session.chain_hash,
        "transcript": session.transcript,
        "transcript_status": session.transcript_status,
    }


def build_package_pdf(
    session: EvidenceSession,
    chunks: list[EvidenceChunk],
    citizen_name: str,
) -> bytes:
    """Chain-of-custody report: metadata, per-chunk hash log, transcript.

    Deliberately in Albanian only — it is an official-style record for
    Kosovo institutions, like the signature certificate (cert_subtitle).
    """
    from weasyprint import HTML

    def fmt(dt: datetime | None) -> str:
        return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC") if dt else "—"

    rows = "".join(
        f"<tr><td>{c.seq + 1}</td><td>{fmt(c.created_at)}</td>"
        f"<td>{c.size_bytes}</td><td class='mono'>{c.sha256}</td>"
        f"<td class='mono'>{c.chain_hash}</td></tr>"
        for c in sorted(chunks, key=lambda c: c.seq)
    )
    chain_ok = verify_chain(list(chunks))
    transcript_html = (
        f"<h2>Transkripti (i gjeneruar automatikisht — Whisper, lokalisht)</h2>"
        f"<p class='transcript'>{escape(session.transcript or '')}</p>"
        if session.transcript
        else ""
    )
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>
      @page {{ size: A4; margin: 18mm 15mm; }}
      body {{ font-family: sans-serif; font-size: 10px; color: #111; }}
      h1 {{ font-size: 16px; margin-bottom: 2px; }}
      h2 {{ font-size: 12px; margin-top: 14px; }}
      .sub {{ color: #555; margin-top: 0; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 6px; }}
      th, td {{ border: 1px solid #ccc; padding: 3px 5px; text-align: left; }}
      th {{ background: #f1f1f4; }}
      .mono {{ font-family: monospace; font-size: 7px; word-break: break-all; }}
      .meta td {{ border: none; padding: 2px 8px 2px 0; }}
      .ok {{ color: #067647; font-weight: bold; }}
      .bad {{ color: #b42318; font-weight: bold; }}
      .transcript {{ white-space: pre-wrap; background: #fafafa;
                     border: 1px solid #eee; padding: 8px; }}
      .note {{ color: #555; margin-top: 12px; font-size: 8.5px; }}
    </style></head><body>
      <h1>PAKO DËSHMIE — AvokatIM</h1>
      <p class="sub">Regjistër i zinxhirit të kujdestarisë (chain of custody)</p>
      <table class="meta">
        <tr><td><b>Sesioni</b></td><td class="mono">{session.id}</td></tr>
        <tr><td><b>Qytetari</b></td><td>{escape(citizen_name)}</td></tr>
        <tr><td><b>Lloji</b></td><td>{session.kind} ({session.mime})</td></tr>
        <tr><td><b>Fillimi</b></td><td>{fmt(session.created_at)}</td></tr>
        <tr><td><b>Mbarimi</b></td><td>{fmt(session.finished_at)}</td></tr>
        <tr><td><b>Copëza / madhësia</b></td>
            <td>{session.chunk_count} copëza · {session.total_bytes} bytes</td></tr>
        <tr><td><b>Hash-i përfundimtar i zinxhirit</b></td>
            <td class="mono">{session.chain_hash or "—"}</td></tr>
        <tr><td><b>Integriteti i zinxhirit</b></td>
            <td class="{'ok' if chain_ok else 'bad'}">
              {"I VERIFIKUAR — asnjë copëz e ndryshuar apo e zhvendosur"
               if chain_ok else "GABIM — zinxhiri NUK verifikohet"}</td></tr>
      </table>
      <h2>Regjistri i copëzave</h2>
      <table>
        <tr><th>#</th><th>Pranuar në server</th><th>Bytes</th>
            <th>SHA-256 e copëzës</th><th>Hash-i i zinxhirit</th></tr>
        {rows}
      </table>
      {transcript_html}
      <p class="note">Si funksionon verifikimi: çdo copëz audio/video u ngarkua
      në server GJATË inçizimit dhe u vulos me kohën e serverit. SHA-256 e çdo
      copëze lidhet me paraardhësen (H<sub>n</sub> = SHA-256(H<sub>n-1</sub> ‖
      SHA-256<sub>n</sub>)), kështu që çdo ndryshim, fshirje apo rirenditje e
      përmbajtjes e prish zinxhirin. Materiali ruhet i enkriptuar në
      infrastrukturën e AvokatIM; transkripti gjenerohet lokalisht dhe audio
      nuk largohet nga serveri.</p>
    </body></html>"""
    return HTML(string=page).write_pdf()
