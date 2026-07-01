"""Simple character-based text chunker with overlap.

Splits on paragraph boundaries where possible, falling back to hard
character cuts for long runs. Good enough for a first RAG pass; a
token-aware splitter can replace this later.
"""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = end - overlap

    return chunks
