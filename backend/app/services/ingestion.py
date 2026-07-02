"""Document ingestion pipeline: extract -> chunk -> store -> index.

Runs synchronously for now. Moving this to a Celery task is a
ROADMAP Milestone 2 item.
"""

from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.services import embeddings, search, vectorstore
from app.services.chunking import chunk_text
from app.services.extraction import extract_text


def process_document(db: Session, document: Document) -> int:
    """Extract text, chunk it, persist chunks, and index them for search.

    Returns the number of chunks produced. Updates document.status.
    """
    text = extract_text(document.storage_path, document.content_type)
    chunks = chunk_text(text)

    if not chunks:
        document.status = "no_text"
        db.commit()
        return 0

    # Persist chunks to Postgres first (source of truth), then index to ES.
    # This ordering avoids ES/PG drift: if indexing fails, the durable rows
    # still exist and can be re-indexed, rather than leaving ES orphans.
    rows = []
    for idx, content in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=document.id,
            owner_id=document.owner_id,
            chunk_index=idx,
            content=content,
        )
        db.add(chunk)
        rows.append(chunk)

    db.flush()  # assign chunk ids
    actions = [
        {
            "chunk_id": chunk.id,
            "document_id": document.id,
            "owner_id": document.owner_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
        }
        for chunk in rows
    ]

    document.status = "indexing"
    db.commit()

    try:
        search.bulk_index_chunks(actions)
        vectors = embeddings.embed_passages([a["content"] for a in actions])
        vectorstore.upsert_chunks(actions, vectors)
    except Exception:
        # Roll back partial writes in both stores so PG stays the single
        # source of truth (rows survive and can be re-indexed later).
        for cleanup in (search.delete_document_chunks, vectorstore.delete_document_chunks):
            try:
                cleanup(document.id)
            except Exception:
                pass
        document.status = "index_failed"
        db.commit()
        raise

    document.status = "processed"
    db.commit()
    return len(chunks)
