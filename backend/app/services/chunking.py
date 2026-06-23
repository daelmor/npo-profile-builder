"""Plain character-window chunking with overlap.

Kept deliberately simple for the MVP: chunks are stored now and embedded for
RAG in Slice 3. Overlap preserves context that would otherwise be split across
a boundary.
"""

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    step = max(size - overlap, 1)
    chunks: list[str] = []
    for start in range(0, len(text), step):
        chunk = text[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= len(text):
            break
    return chunks
