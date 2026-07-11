"""Dense embeddings via sentence-transformers.

Model is loaded lazily on first use and cached for the process lifetime —
loading bge-m3 takes seconds and must not happen at import time (it would
slow app boot and break environments without the model downloaded).

bge-family models expect a query instruction prefix for retrieval queries
but plain text for passages.
"""

from sentence_transformers import SentenceTransformer

from app.core.config import settings

_model: SentenceTransformer | None = None

_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model_name)
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    model = get_model()
    vector = model.encode(_QUERY_PREFIX + text, normalize_embeddings=True, show_progress_bar=False)
    return vector.tolist()
