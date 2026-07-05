"""Cross-encoder re-ranking (BAAI/bge-reranker-v2-m3, blueprint choice).

Bi-encoder retrieval (bge-m3) scores query and passage independently —
fast but lossy. The cross-encoder reads query+passage together, giving a
much sharper relevance signal. Standard pattern: overfetch candidates
with cheap retrieval, rerank the top few dozen with this model.

Lazy singleton like embeddings/ocr (~2.3GB download on first use).
"""

from app.core.config import settings

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(settings.reranker_model_name)
    return _model


def rerank(query: str, hits: list[dict], top_k: int) -> list[dict]:
    """Order hits by cross-encoder relevance, keep top_k.

    Adds `rerank_score` to each returned hit; original retrieval score is
    preserved in `score`.
    """
    if not hits:
        return []
    model = get_model()
    scores = model.predict([(query, hit["content"]) for hit in hits])
    for hit, score in zip(hits, scores):
        hit["rerank_score"] = float(score)
    ranked = sorted(hits, key=lambda h: h["rerank_score"], reverse=True)
    return ranked[:top_k]
