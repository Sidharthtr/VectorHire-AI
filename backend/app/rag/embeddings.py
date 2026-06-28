"""
Text embedding layer — turns strings into dense vectors for semantic search.

What it does:
- Lazy-loads a SentenceTransformer model (singleton) and exposes embed_text / embed_batch.
- Sits at the very start of the RAG pipeline: every document ingested and every
  query issued passes through here before it can hit the vector DB.

Upstream (who imports this): app/rag/dense_retriever.py, app/rag/retriever.py,
    app/services/embedding_service.py, app/services/ingestion_service.py,
    app/ingestion/job_embedder.py
Downstream (what this imports): sentence-transformers, numpy, app.core.constants
"""
from __future__ import annotations
# SentenceTransformer: HuggingFace model wrapper that produces normalized embeddings
from sentence_transformers import SentenceTransformer
# Union: legacy typing import kept for compatibility (not actively used below)
from typing import Union
# numpy: SentenceTransformer returns ndarrays; we convert them to plain lists
import numpy as np
# EMBEDDING_MODEL: model name string (e.g. "all-MiniLM-L6-v2") loaded from config
from app.core.constants import EMBEDDING_MODEL
# get_logger: structured logger so model-load events show up in app logs
from app.core.logging import get_logger

logger = get_logger(__name__)

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded")
    return _model


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return embeddings.tolist()
