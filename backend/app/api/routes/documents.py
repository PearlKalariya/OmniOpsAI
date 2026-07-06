import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.ratelimit import limiter
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.agents import document_agent
from app.schemas.document import AskRequest, AskResponse, DocumentOut, SearchHit
from app.services import embeddings, hybrid, llm, reranker, search, vectorstore
from app.tasks.ingestion import ingest_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/csv",
    "text/plain",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "video/mp4",
}

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_SEARCH_RESULTS = 50


@router.post("/upload", response_model=DocumentOut, status_code=201)
@limiter.limit("20/minute")  # ingestion runs embeddings/OCR — expensive
async def upload_document(
    request: Request,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {file.content_type}")

    # Read with a cap so an oversized upload can't exhaust memory. Reading
    # MAX+1 bytes lets us detect "too large" without loading the whole body.
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 25 MB)")

    # Content-Type is client-supplied and spoofable; verify magic bytes for
    # formats we parse so a mislabeled payload can't reach the wrong parser.
    if file.content_type == "application/pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="File does not look like a valid PDF")

    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1]
    stored_name = f"{uuid.uuid4()}{ext}"
    storage_path = os.path.join(settings.upload_dir, stored_name)

    with open(storage_path, "wb") as f:
        f.write(content)

    document = Document(
        owner_id=current_user.id,
        filename=file.filename or stored_name,
        storage_path=storage_path,
        content_type=file.content_type,
        status="queued",
        size_bytes=len(content),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    if settings.ingest_sync:
        _ingest_inline(db, document)
    else:
        try:
            ingest_document.delay(document.id)
        except Exception as exc:
            # Broker unreachable — degrade to inline processing rather than
            # stranding the document in "queued".
            logger.warning("Celery enqueue failed (%s); ingesting inline", exc)
            _ingest_inline(db, document)
    db.refresh(document)
    return document


def _ingest_inline(db: Session, document: Document) -> None:
    # Upload already succeeded, so a processing failure marks the document
    # rather than failing the request.
    try:
        document_agent.process(db, document)
    except Exception:
        logger.exception("Inline ingestion failed for document %s", document.id)
        db.rollback()
        document.status = "failed"
        db.commit()


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Document).filter(Document.owner_id == current_user.id).all()


@router.get("/search", response_model=list[SearchHit])
def search_documents(
    q: str,
    limit: int = 5,
    mode: str = "hybrid",
    rerank: bool = False,
    current_user: User = Depends(get_current_user),
):
    limit = max(1, min(limit, MAX_SEARCH_RESULTS))
    fetch = limit * 3 if rerank else limit
    if mode == "bm25":
        hits = search.search_chunks(owner_id=current_user.id, query=q, size=fetch)
    elif mode == "vector":
        query_vector = embeddings.embed_query(q)
        hits = vectorstore.search_chunks(owner_id=current_user.id, query_vector=query_vector, size=fetch)
    elif mode == "hybrid":
        hits = hybrid.hybrid_search(owner_id=current_user.id, query=q, size=fetch)
    else:
        raise HTTPException(status_code=422, detail="mode must be one of: hybrid, bm25, vector")
    if rerank:
        hits = reranker.rerank(q, hits, top_k=limit)
    return hits


@router.post("/ask", response_model=AskResponse)
@limiter.limit("20/minute")  # each call is a paid/quota'd LLM request
def ask_documents(
    request: Request,
    payload: AskRequest,
    current_user: User = Depends(get_current_user),
):
    if not llm.is_configured():
        raise HTTPException(
            status_code=503,
            detail="LLM not configured: set LLM_API_KEY in backend/.env",
        )

    limit = max(1, min(payload.limit, MAX_SEARCH_RESULTS))
    hits = hybrid.hybrid_search(owner_id=current_user.id, query=payload.question, size=limit)
    if not hits:
        raise HTTPException(status_code=404, detail="No relevant documents found for this question")

    try:
        result = llm.generate_answer(question=payload.question, chunks=hits)
    except Exception as exc:
        # Full provider error (may contain internal details) goes to logs only.
        logger.exception("LLM request failed")
        raise HTTPException(
            status_code=502,
            detail=f"LLM request failed ({type(exc).__name__}); see server logs",
        ) from exc

    return AskResponse(answer=result["answer"], model=result["model"], sources=hits)


# Keep this LAST: /{document_id} would otherwise shadow /search and /ask
# (Starlette matches routes in registration order).
@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)
    if document is None or document.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
