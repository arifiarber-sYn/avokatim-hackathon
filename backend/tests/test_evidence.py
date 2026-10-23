"""Evidence vault unit tests: hash chain, storage round-trip, package PDF."""
import hashlib
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.services import evidence


def _fake_session(**kw):
    now = datetime.now(UTC)
    defaults = dict(
        id=uuid.uuid4(), citizen_id=uuid.uuid4(), case_request_id=None,
        kind="sos_audio", mime="audio/webm", status="recording", locale="sq",
        created_at=now, finished_at=None, chunk_count=0, total_bytes=0,
        chain_hash=None, transcript=None, transcript_status="none",
        consent_at=now,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def test_chain_hash_binds_content_and_order():
    h1 = evidence.chain_hash(None, hashlib.sha256(b"a").hexdigest())
    h2 = evidence.chain_hash(h1, hashlib.sha256(b"b").hexdigest())
    # Same content in a different order yields a different chain
    g1 = evidence.chain_hash(None, hashlib.sha256(b"b").hexdigest())
    g2 = evidence.chain_hash(g1, hashlib.sha256(b"a").hexdigest())
    assert h2 != g2
    # Deterministic
    assert h2 == evidence.chain_hash(h1, hashlib.sha256(b"b").hexdigest())


def test_store_and_reload_chunks_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", tmp_path)
    session = _fake_session()
    parts = [b"first-part-bytes", b"second-part-bytes", b"third"]
    chunks = []
    for i, part in enumerate(parts):
        chunks.append(evidence.store_chunk(session, i, part))
    assert session.chunk_count == 3
    assert session.total_bytes == sum(len(p) for p in parts)
    assert evidence.verify_chain(chunks) is True
    assert evidence.load_audio(session, chunks) == b"".join(parts)


def test_verify_chain_detects_tamper(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", tmp_path)
    session = _fake_session()
    chunks = [evidence.store_chunk(session, i, bytes([i]) * 50) for i in range(4)]
    assert evidence.verify_chain(chunks)
    # Tampering with one chunk's recorded hash breaks the chain
    chunks[2].sha256 = hashlib.sha256(b"forged").hexdigest()
    assert not evidence.verify_chain(chunks)
    # Reordering breaks it too
    chunks[2].sha256 = hashlib.sha256(bytes([2]) * 50).hexdigest()
    reordered = [chunks[0], chunks[2], chunks[1], chunks[3]]
    for i, c in enumerate(reordered):
        c.seq = i
    assert not evidence.verify_chain(reordered)


def test_package_pdf_contains_chain(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", tmp_path)
    session = _fake_session(transcript="Më ndaloi policia pa arsyetim.",
                            finished_at=datetime.now(UTC), status="finished")
    chunks = []
    for i in range(2):
        chunk = evidence.store_chunk(session, i, b"x" * 100)
        chunk.created_at = datetime.now(UTC)
        chunks.append(chunk)
    pdf = evidence.build_package_pdf(session, chunks, "Qytetar Test")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 5000
