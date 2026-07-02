"""Qdrant dense-vector storage and search for document chunks.

The dense half of hybrid retrieval (BM25 half lives in search.py).
Chunk UUIDs are reused as Qdrant point ids so PG stays the source of
truth and cleanup is symmetric with Elasticsearch.
"""

from qdrant_client import QdrantClient
from qdrant_client import models as qm

from app.core.config import settings

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.qdrant_url)
    return _client


def ensure_collection(dim: int) -> None:
    client = get_client()
    if client.collection_exists(settings.qdrant_collection):
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
    )
    # Payload indexes make the owner/document filters cheap.
    client.create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="owner_id",
        field_schema=qm.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="document_id",
        field_schema=qm.PayloadSchemaType.KEYWORD,
    )


def upsert_chunks(chunks: list[dict], vectors: list[list[float]]) -> None:
    """Store chunk vectors. chunks dicts need chunk_id/document_id/owner_id/chunk_index/content."""
    client = get_client()
    ensure_collection(dim=len(vectors[0]))
    points = [
        qm.PointStruct(
            id=chunk["chunk_id"],
            vector=vector,
            payload={
                "document_id": chunk["document_id"],
                "owner_id": chunk["owner_id"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
            },
        )
        for chunk, vector in zip(chunks, vectors)
    ]
    client.upsert(collection_name=settings.qdrant_collection, points=points, wait=True)


def delete_document_chunks(document_id: str) -> None:
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=qm.FilterSelector(
            filter=qm.Filter(must=[qm.FieldCondition(key="document_id", match=qm.MatchValue(value=document_id))])
        ),
        wait=True,
    )


def search_chunks(owner_id: str, query_vector: list[float], size: int = 5) -> list[dict]:
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return []
    hits = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=qm.Filter(must=[qm.FieldCondition(key="owner_id", match=qm.MatchValue(value=owner_id))]),
        limit=size,
    ).points
    return [
        {
            "chunk_id": str(hit.id),
            "score": hit.score,
            "document_id": hit.payload["document_id"],
            "chunk_index": hit.payload["chunk_index"],
            "content": hit.payload["content"],
        }
        for hit in hits
    ]
