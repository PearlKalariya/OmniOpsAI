"""Elasticsearch BM25 indexing and search for document chunks.

This is the lexical half of the planned hybrid retriever. Dense vector
search (Qdrant + bge-m3) and cross-encoder re-ranking come later.
"""

from elasticsearch import Elasticsearch, helpers

from app.core.config import settings

_client: Elasticsearch | None = None


def get_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(settings.elasticsearch_url)
    return _client


def ensure_index() -> None:
    client = get_client()
    if client.indices.exists(index=settings.es_chunk_index):
        return
    client.indices.create(
        index=settings.es_chunk_index,
        mappings={
            "properties": {
                "document_id": {"type": "keyword"},
                "owner_id": {"type": "keyword"},
                "chunk_index": {"type": "integer"},
                "content": {"type": "text"},
            }
        },
    )


def bulk_index_chunks(chunks: list[dict]) -> None:
    """Index a batch of chunks in one round trip.

    Each dict must have: chunk_id, document_id, owner_id, chunk_index, content.
    refresh="wait_for" makes the docs searchable before returning, so a
    search immediately after ingestion sees them.
    """
    client = get_client()
    ensure_index()
    actions = [
        {
            "_index": settings.es_chunk_index,
            "_id": c["chunk_id"],
            "_source": {
                "document_id": c["document_id"],
                "owner_id": c["owner_id"],
                "chunk_index": c["chunk_index"],
                "content": c["content"],
            },
        }
        for c in chunks
    ]
    helpers.bulk(client, actions, refresh="wait_for")


def delete_document_chunks(document_id: str) -> None:
    """Remove all ES docs for a document (used to undo a partial index)."""
    client = get_client()
    client.delete_by_query(
        index=settings.es_chunk_index,
        query={"term": {"document_id": document_id}},
        conflicts="proceed",
    )


def search_chunks(owner_id: str, query: str, size: int = 5) -> list[dict]:
    client = get_client()
    ensure_index()
    response = client.search(
        index=settings.es_chunk_index,
        query={
            "bool": {
                "must": {"match": {"content": query}},
                "filter": {"term": {"owner_id": owner_id}},
            }
        },
        size=size,
    )
    hits = response["hits"]["hits"]
    return [
        {
            "chunk_id": hit["_id"],
            "score": hit["_score"],
            "document_id": hit["_source"]["document_id"],
            "chunk_index": hit["_source"]["chunk_index"],
            "content": hit["_source"]["content"],
        }
        for hit in hits
    ]
