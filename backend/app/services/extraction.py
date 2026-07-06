"""Text + metadata extraction from uploaded files.

Handles text-based PDFs, CSVs, plain text, images (BLIP caption + TrOCR
text, see vision.py/ocr.py), and audio (faster-whisper, see stt.py).
Video needs a demux step first (future Vision/Audio work).
"""

import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)

IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg"}
AUDIO_CONTENT_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4"}


def extract_text(path: str, content_type: str) -> tuple[str, dict]:
    """Return (text, metadata). Metadata keys: page_count, char_count."""
    if content_type == "application/pdf":
        text, pages = _extract_pdf(path)
        return text, {"page_count": pages, "char_count": len(text)}
    if content_type in ("text/csv", "text/plain"):
        text = _extract_plain(path)
        return text, {"page_count": None, "char_count": len(text)}
    if content_type in IMAGE_CONTENT_TYPES:
        from app.services import ocr, vision

        # Caption says what the image shows; OCR reads the text in it.
        # Both go into the chunk so either kind of query finds the image.
        parts = []
        try:
            described = vision.caption(path)
            if described:
                parts.append(f"Image description: {described}")
        except Exception as exc:  # captioning is best-effort; OCR still indexes
            logger.warning("Captioning failed for %s: %s", path, exc)
        extracted = ocr.image_to_text(path)
        if extracted:
            parts.append(f"Text in image: {extracted}")
        text = "\n".join(parts)
        return text, {"page_count": None, "char_count": len(text)}
    if content_type in AUDIO_CONTENT_TYPES:
        from app.services import stt

        text, _meta = stt.transcribe(path)
        return text, {"page_count": None, "char_count": len(text)}
    return "", {"page_count": None, "char_count": 0}


def _extract_pdf(path: str) -> tuple[str, int]:
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip(), len(pages)


def _extract_plain(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().strip()
