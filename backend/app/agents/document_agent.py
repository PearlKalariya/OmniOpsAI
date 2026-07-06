"""Document Agent (blueprint role: PDFs, contracts, manuals, policies).

Facade over the document-processing capabilities so callers depend on
the agent, not on individual services:

    capabilities: OCR (ocr.py) + STT (stt.py) -> extraction -> chunking
                  -> metadata -> dual indexing (BM25 + vectors)

The Celery ingestion task and any future graph nodes route through this
module. Retrieval stays with the Retrieval Agent (agents/nodes.py).
"""

from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.extraction import AUDIO_CONTENT_TYPES, IMAGE_CONTENT_TYPES
from app.services.ingestion import process_document

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "text/csv",
    "text/plain",
} | IMAGE_CONTENT_TYPES | AUDIO_CONTENT_TYPES


def process(db: Session, document: Document) -> int:
    """Run the full document pipeline; returns chunk count."""
    return process_document(db, document)


def supports(content_type: str) -> bool:
    return content_type in SUPPORTED_CONTENT_TYPES
