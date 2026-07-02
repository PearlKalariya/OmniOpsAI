"""Hybrid retrieval: BM25 (Elasticsearch) + dense vectors (Qdrant), fused
with Reciprocal Rank Fusion.

RRF combines rankings without needing to normalize the incompatible score
scales (BM25 is unbounded, cosine is [-1, 1]): each hit contributes
1 / (k + rank) per list it appears in. k=60 is the standard constant from
the original RRF paper and dampens the impact of top-rank differences.
"""

from app.services import embeddings, search, vectorstore

RRF_K = 60

# Fetch more candidates than requested from each retriever so fusion has
# overlap to work with; a hit ranked low in both lists can still win.
CANDIDATE_MULTIPLIER = 3


def hybrid_search(owner_id: str, query: str, size: int = 5) -> list[dict]:
    candidates = size * CANDIDATE_MULTIPLIER

    bm25_hits = search.search_chunks(owner_id=owner_id, query=query, size=candidates)
    query_vector = embeddings.embed_query(query)
    vector_hits = vectorstore.search_chunks(owner_id=owner_id, query_vector=query_vector, size=candidates)

    fused: dict[str, dict] = {}
    for source, hits in (("bm25", bm25_hits), ("vector", vector_hits)):
        for rank, hit in enumerate(hits):
            entry = fused.setdefault(
                hit["chunk_id"],
                {
                    "chunk_id": hit["chunk_id"],
                    "document_id": hit["document_id"],
                    "chunk_index": hit["chunk_index"],
                    "content": hit["content"],
                    "score": 0.0,
                    "sources": [],
                },
            )
            entry["score"] += 1.0 / (RRF_K + rank + 1)
            entry["sources"].append(source)

    ranked = sorted(fused.values(), key=lambda e: e["score"], reverse=True)
    return ranked[:size]
