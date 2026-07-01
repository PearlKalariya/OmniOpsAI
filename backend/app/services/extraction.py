"""Text extraction from uploaded files.

Handles text-based PDFs, CSVs, and plain text. Scanned-image OCR (TrOCR)
is deferred — see ROADMAP Milestone 1.
"""

from pypdf import PdfReader


def extract_text(path: str, content_type: str) -> str:
    if content_type == "application/pdf":
        return _extract_pdf(path)
    if content_type in ("text/csv", "text/plain"):
        return _extract_plain(path)
    # Images/audio/video need OCR/STT pipelines (not yet implemented).
    return ""


def _extract_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _extract_plain(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().strip()
