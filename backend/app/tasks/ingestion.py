"""Celery task wrapping the ingestion pipeline.

The task owns its DB session (request session is gone by the time the
worker runs). process_document already handles per-store cleanup and
status transitions; this layer adds the final failure catch so a crashed
task never leaves a document stuck in "queued".
"""

import logging

import app.models  # noqa: F401 — full model registry for FK resolution
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.document import Document
from app.services.ingestion import process_document

logger = logging.getLogger(__name__)


@celery_app.task(name="ingest_document", max_retries=2, default_retry_delay=10)
def ingest_document(document_id: str) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            logger.error("ingest_document: document %s not found", document_id)
            return
        try:
            process_document(db, document)
        except Exception:
            logger.exception("Ingestion failed for document %s", document_id)
            db.rollback()
            document = db.get(Document, document_id)
            if document is not None and document.status not in ("processed", "no_text"):
                document.status = "failed"
                db.commit()
    finally:
        db.close()
