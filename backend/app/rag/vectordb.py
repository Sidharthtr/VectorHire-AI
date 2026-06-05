"""
ChromaDB client — supports two modes controlled by USE_CHROMADB_SERVER:

  False (default, local dev):
      PersistentClient — embedded, stores data in app/data/chroma/
      No Docker needed. Good for development.

  True (Docker / production):
      HttpClient — connects to a separate ChromaDB container.
      Allows multiple backend workers to share the same vector store.
      Set CHROMADB_HOST and CHROMADB_PORT accordingly.

The rest of the app never imports chromadb directly — everything goes
through get_chroma_client(), get_jobs_collection(), etc.
"""
from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
from typing import Optional

from app.core.constants import CHROMA_DIR, CHROMA_COLLECTION_JOBS, CHROMA_COLLECTION_RESUMES
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: chromadb.Client | None = None


def get_chroma_client() -> chromadb.Client:
    global _client
    if _client is None:
        from app.core.settings import get_settings
        settings = get_settings()

        if settings.use_chromadb_server:
            # Docker / production mode — connect to ChromaDB HTTP server
            logger.info(f"Connecting to ChromaDB server at {settings.chromadb_host}:{settings.chromadb_port}")
            _client = chromadb.HttpClient(
                host=settings.chromadb_host,
                port=settings.chromadb_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        else:
            # Local dev mode — embedded persistent client
            persist_dir = str(CHROMA_DIR)
            Path(persist_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Connecting to ChromaDB (embedded) at {persist_dir}")
            _client = chromadb.PersistentClient(
                path=persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
    return _client


def get_jobs_collection() -> chromadb.Collection:
    return get_chroma_client().get_or_create_collection(
        name=CHROMA_COLLECTION_JOBS,
        metadata={"hnsw:space": "cosine"},
    )


def get_resumes_collection() -> chromadb.Collection:
    return get_chroma_client().get_or_create_collection(
        name=CHROMA_COLLECTION_RESUMES,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_documents(
    collection: chromadb.Collection,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    logger.info(f"Upserted {len(ids)} documents into '{collection.name}'")


def query_collection(
    collection: chromadb.Collection,
    query_embedding: list[float],
    top_k: int = 10,
    where: Optional[dict] = None,
) -> dict:
    kwargs = dict(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count() or 1),
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def reset_collection(collection_name: str) -> None:
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        logger.info(f"Deleted collection: {collection_name}")
    except Exception:
        pass
    client.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine"})
    logger.info(f"Re-created collection: {collection_name}")


def reset_client() -> None:
    """Force re-initialise the client (used in tests or after config changes)."""
    global _client
    _client = None
