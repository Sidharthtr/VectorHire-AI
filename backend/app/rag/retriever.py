from app.rag.vectordb import get_jobs_collection, query_collection
from app.rag.embeddings import embed_text
from app.schemas.job_schema import JobDocument
from app.core.constants import DEFAULT_TOP_K, SIMILARITY_THRESHOLD
from app.core.logging import get_logger
from typing import Optional

logger = get_logger(__name__)


def retrieve_jobs(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    experience_level: Optional[str] = None,
) -> list[tuple[JobDocument, float]]:
    """Embed query and retrieve matching jobs from ChromaDB."""
    query_embedding = embed_text(query)
    collection = get_jobs_collection()

    where_filter = None
    if experience_level:
        where_filter = {"experience_level": experience_level}

    results = query_collection(collection, query_embedding, top_k=top_k, where=where_filter)

    jobs_with_scores = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite. Convert to similarity.
        similarity = 1.0 - (distance / 2.0)
        if similarity < SIMILARITY_THRESHOLD:
            continue

        try:
            job = JobDocument(
                id=metadata.get("job_id", doc_id),
                title=metadata.get("title", "Unknown"),
                company=metadata.get("company", "Unknown"),
                location=metadata.get("location", "Remote"),
                experience_level=metadata.get("experience_level", "entry"),
                employment_type=metadata.get("employment_type", "full-time"),
                skills=_parse_list_field(metadata.get("skills", "")),
                description=document,
                remote=metadata.get("remote", False),
                salary_range=metadata.get("salary_range"),
            )
            jobs_with_scores.append((job, similarity))
        except Exception as e:
            logger.warning(f"Failed to parse job {doc_id}: {e}")
            continue

    logger.info(f"Retrieved {len(jobs_with_scores)} jobs for query: '{query[:60]}'")
    return jobs_with_scores


def _parse_list_field(value: str | list) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        return [s.strip() for s in value.split(",") if s.strip()]
    return []
