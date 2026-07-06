"""Document storage: content-addressed files under data/documents/, optional
Fernet encryption at rest, text extraction (native PDF text, OCR fallback)."""
import base64
import hashlib
import logging
import uuid
from io import BytesIO
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings

logger = logging.getLogger(__name__)

_SALT = b"boralaw-document-storage-v1"


def _fernet() -> Fernet | None:
    if not settings.doc_encryption_key:
        return None
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=600_000)
    key = base64.urlsafe_b64encode(kdf.derive(settings.doc_encryption_key.encode()))
    return Fernet(key)


def save_file(content: bytes, tenant_id: uuid.UUID) -> tuple[str, str, bool]:
    """Store bytes; returns (relative_path, sha256, encrypted)."""
    sha = hashlib.sha256(content).hexdigest()
    fernet = _fernet()
    stored = fernet.encrypt(content) if fernet else content

    rel = Path(str(tenant_id)) / sha[:2] / sha
    full = settings.documents_dir / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    if not full.exists():
        full.write_bytes(stored)
    return str(rel), sha, fernet is not None


def load_file(relative_path: str, encrypted: bool) -> bytes:
    content = (settings.documents_dir / relative_path).read_bytes()
    if encrypted:
        fernet = _fernet()
        if fernet is None:
            raise RuntimeError("Document is encrypted but no doc_encryption_key is set")
        content = fernet.decrypt(content)
    return content


def extract_text(content: bytes, mime_type: str, filename: str) -> tuple[str, str]:
    """Best-effort text extraction. Returns (text, ocr_status)."""
    name = filename.lower()
    if mime_type.startswith("text/") or name.endswith((".txt", ".md")):
        return content.decode("utf-8", errors="replace"), "none"

    if mime_type == "application/pdf" or name.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
            if len(text) > 50:
                return text, "none"
        except Exception as exc:
            logger.warning("PDF text extraction failed for %s: %s", filename, exc)
        ocr = _ocr_pdf(content)
        if ocr is not None:
            return ocr, "done"
        return "", "pending"

    if mime_type.startswith("image/"):
        ocr = _ocr_image(content)
        if ocr is not None:
            return ocr, "done"
        return "", "pending"

    return "", "none"


def _ocr_image(content: bytes) -> str | None:
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(BytesIO(content))
        return pytesseract.image_to_string(image, lang=settings.ocr_languages)
    except Exception as exc:
        logger.warning("OCR unavailable or failed: %s", exc)
        return None


def _ocr_pdf(content: bytes) -> str | None:
    """OCR a scanned PDF by rasterizing pages (requires pypdf + Pillow-compatible
    rendering via pdf images). Kept simple: extract embedded images per page."""
    try:
        import pytesseract
        from PIL import Image
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        texts = []
        for page in reader.pages:
            for img in page.images:
                try:
                    pil = Image.open(BytesIO(img.data))
                    texts.append(pytesseract.image_to_string(pil, lang=settings.ocr_languages))
                except Exception:
                    continue
        joined = "\n\n".join(t for t in texts if t.strip())
        return joined if joined.strip() else None
    except Exception as exc:
        logger.warning("PDF OCR unavailable or failed: %s", exc)
        return None
