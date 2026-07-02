import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import AskRequest, AskResponse, DocumentOut, SearchHit
from app.services import embeddings, hybrid, llm, search, vectorstore
from app.services.ingestion import process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/csv",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
}

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_SEARCH_RESULTS = 50


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
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
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Ingest synchronously. Upload already succeeded, so a processing
    # failure marks the document rather than failing the request.
    try:
        process_document(db, document)
    except Exception:
        db.rollback()
        document.status = "failed"
        db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Document).filter(Document.owner_id == current_user.id).all()


@router.get("/search", response_model=list[SearchHit])
def search_documents(
    q: str,
    limit: int = 5,
    mode: str = "hybrid",
    current_user: User = Depends(get_current_user),
):
    limit = max(1, min(limit, MAX_SEARCH_RESULTS))
    if mode == "bm25":
        return search.search_chunks(owner_id=current_user.id, query=q, size=limit)
    if mode == "vector":
        query_vector = embeddings.embed_query(q)
        return vectorstore.search_chunks(owner_id=current_user.id, query_vector=query_vector, size=limit)
    if mode == "hybrid":
        return hybrid.hybrid_search(owner_id=current_user.id, query=q, size=limit)
    raise HTTPException(status_code=422, detail="mode must be one of: hybrid, bm25, vector")


@router.post("/ask", response_model=AskResponse)
def ask_documents(
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
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc

    return AskResponse(answer=result["answer"], model=result["model"], sources=hits)
