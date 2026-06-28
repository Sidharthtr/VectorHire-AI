"""
Dense (semantic) retriever — vector-space half of the hybrid RAG pipeline.

What it does:
- Embeds the user query, runs a cosine-similarity search against the jobs collection,
  applies optional metadata filters, dedupes by job_id, and returns ranked JobDocuments.
- Sits between vectordb (raw Chroma) and hybrid_retriever (which fuses dense+sparse).

Upstream (who imports this): app/rag/hybrid_retriever.py
Downstream (what this imports): app.rag.vectordb (Chroma access), app.rag.embeddings
    (query vectorization), app.schemas.job_schema, app.core.constants
"""
from __future__ import annotations
# vectordb helpers: jobs collection handle + thin query wrapper around Chroma
from app.rag.vectordb import get_jobs_collection, query_collection
# embed_text: turns the query string into the dense vector we search with
from app.rag.embeddings import embed_text
# JobDocument: the Pydantic shape we hydrate each Chroma hit into before returning
from app.schemas.job_schema import JobDocument
# DEFAULT_TOP_K + SIMILARITY_THRESHOLD: tunables for result size and min score
from app.core.constants import DEFAULT_TOP_K, SIMILARITY_THRESHOLD
# get_logger: structured debug logging of result counts per query
from app.core.logging import get_logger
# Optional: type hint for the optional experience_level filter argument
from typing import Optional

logger = get_logger(__name__)


def _parse_list_field(value) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return []


def _build_where(
    experience_level: Optional[str],
    remote_only: bool,
) -> Optional[dict]:
    """Build ChromaDB where filter from optional constraints."""
    conditions = []
    if experience_level:
        conditions.append({"experience_level": {"$eq": experience_level}})
    if remote_only:
        conditions.append({"remote": {"$eq": True}})
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def dense_retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    experience_level: Optional[str] = None,
    remote_only: bool = False,
) -> list[tuple[JobDocument, float, int]]:
    """
    Semantic search via ChromaDB.
    Returns list of (JobDocument, similarity_score, rank) sorted best-first.
    """
    collection = get_jobs_collection()
    query_vec = embed_text(query)

    where = _build_where(experience_level, remote_only)
    results = query_collection(collection, query_vec, top_k=top_k * 3, where=where)

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
        ranked.append((job, similarity, 0))

        if len(ranked) >= top_k:
            break

    ranked = [(job, score, i + 1) for i, (job, score, _) in enumerate(ranked)]
    logger.debug(f"Dense retrieval: {len(ranked)} results for '{query[:60]}'")
    return ranked
