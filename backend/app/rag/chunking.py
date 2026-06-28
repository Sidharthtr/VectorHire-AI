"""
Document chunking utility — splits long text into overlapping windows.

What it does:
- chunk_text(): word-count windowing with configurable overlap so context isn't lost
  at boundaries (a classic RAG preprocessing step).
- chunk_document(): attaches metadata + a stable chunk id to each window so they can
  be upserted into Chroma alongside their parent document.
- Sits at ingestion time, BEFORE embeddings/vectordb — long resumes/job specs get
  broken into manageable pieces so the embedding model isn't truncating them.

Upstream (who imports this): app/services/ingestion_service.py
Downstream (what this imports): app.core.constants (CHUNK_SIZE, CHUNK_OVERLAP tunables)
"""
# CHUNK_SIZE + CHUNK_OVERLAP: tunables for window length and slide-back in words
from app.core.constants import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap

    return chunks


def chunk_document(doc_id: str, text: str, metadata: dict) -> list[dict]:
    """Chunk a document and attach metadata to each chunk."""
    chunks = chunk_text(text)
    return [
        {
            "id": f"{doc_id}_chunk_{i}",
            "text": chunk,
            "metadata": {**metadata, "chunk_index": i, "total_chunks": len(chunks)},
        }
        for i, chunk in enumerate(chunks)
    ]
