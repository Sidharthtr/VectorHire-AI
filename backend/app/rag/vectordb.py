import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
from typing import Optional
from app.core.constants import CHROMA_DIR, CHROMA_COLLECTION_JOBS, CHROMA_COLLECTION_RESUMES
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: chromadb.PersistentClient | None = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        persist_dir = str(CHROMA_DIR)
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Connecting to ChromaDB at {persist_dir}")
        _client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_jobs_collection() -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_JOBS,
        metadata={"hnsw:space": "cosine"},
    )


def get_resumes_collection() -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
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
