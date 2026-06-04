"""
Dense (semantic) retriever — wrapper around ChromaDB cosine similarity search.

This is an extraction of the original retriever.py logic into a standalone module
so it can be composed with sparse retrieval in the hybrid pipeline.

Input:  query string + optional filters
Output: list of (JobDocument, similarity_score, rank)
"""
from __future__ import annotations
from app.rag.vectordb import get_jobs_collection, query_collection
from app.rag.embeddings import embed_text
from app.schemas.job_schema import JobDocument
from app.core.constants import DEFAULT_TOP_K, SIMILARITY_THRESHOLD
from app.core.logging import get_logger
from typing import Optional

logger = get_logger(__name__)


def _parse_list_field(value) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return []


def dense_retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    experience_level: Optional[str] = None,
) -> list[tuple[JobDocument, float, int]]:
    """
    Semantic search via ChromaDB.
    Returns list of (JobDocument, similarity_score, rank) sorted best-first.
    """
    collection = get_jobs_collection()
    query_vec = embed_text(query)

    where = {"experience_level": experience_level} if experience_level else None
    results = query_collection(collection, query_vec, top_k=top_k * 2, where=where)

    ids_list       = results.get("ids", [[]])[0]
    distances_list = results.get("distances", [[]])[0]
    metadatas_list = results.get("metadatas", [[]])[0]

    seen_job_ids: set[str] = set()
    ranked: list[tuple[JobDocument, float, int]] = []

    for raw_id, dist, meta in zip(ids_list, distances_list, metadatas_list):
        job_id = meta.get("job_id", raw_id)
        if job_id in seen_job_ids:
            continue
        seen_job_ids.add(job_id)

        similarity = round(1.0 - (dist / 2.0), 4)
        if similarity < SIMILARITY_THRESHOLD:
            continue

        job = JobDocument(
            id=job_id,
            title=meta.get("title", ""),
            company=meta.get("company", ""),
            location=meta.get("location", ""),
            experience_level=meta.get("experience_level", "entry"),
            employment_type=meta.get("employment_type", "full-time"),
            skills=_parse_list_field(meta.get("skills", [])),
            description=meta.get("description", ""),
            remote=meta.get("remote", False),
            salary_range=meta.get("salary_range"),
        )
        ranked.append((job, similarity, 0))  # rank filled below

        if len(ranked) >= top_k:
            break

    # Assign ranks (1-indexed)
    ranked = [(job, score, i + 1) for i, (job, score, _) in enumerate(ranked)]
    logger.debug(f"Dense retrieval: {len(ranked)} results for '{query[:60]}'")
    return ranked
