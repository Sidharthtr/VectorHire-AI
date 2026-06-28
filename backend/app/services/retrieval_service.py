"""
Facade over the hybrid retriever (semantic + BM25) with Redis search caching.

What it does:
- Wraps hybrid_retrieve / retrieve_for_pipeline so the API and graph never call the raw RAG layer.
- Caches search results in Redis keyed by (query, experience, top_k, remote, location, mode) for 1 hour.
- Post-filters by location (ChromaDB lacks substring filters) by overfetching 3x then trimming.
- Builds a resume-derived query string for the graph's retrieve_jobs node.

Upstream (who imports this): app/graph/nodes/retrieve_jobs_node.py, app/api/routes/search_routes.py, debug routes
Downstream (what this imports): app.rag.hybrid_retriever, JobDocument, constants, redis_client, settings, logging
"""
from __future__ import annotations

# json: not used at runtime here but kept available for ad-hoc debug printing of cached payloads
import json
# Optional: experience_level / location are nullable filter inputs
from typing import Optional

# hybrid_retrieve: debug variant returning full HybridResult; retrieve_for_pipeline: production variant returning (job, score) tuples
from app.rag.hybrid_retriever import hybrid_retrieve, retrieve_for_pipeline, HybridResult
# JobDocument: typed shape we deserialize cached search hits into
from app.schemas.job_schema import JobDocument
# DEFAULT_TOP_K: page size default when caller doesn't specify
from app.core.constants import DEFAULT_TOP_K
# get_logger: log cache hits/misses + query previews for retrieval debugging
from app.core.logging import get_logger
# Redis primitives — cache_delete_pattern is used to invalidate all search:* keys after re-ingestion
from app.core.redis_client import cache_get, cache_set, cache_delete_pattern, make_hash
# get_settings: pull retrieval_mode (hybrid/semantic/keyword) and TTLs into the cache key
from app.core.settings import get_settings

_LOCATION_FETCH_MULTIPLIER = 3   # fetch this many times top_k then post-filter by location

logger = get_logger(__name__)


class RetrievalService:
    def search_jobs(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        experience_level: Optional[str] = None,
        remote_only: bool = False,
        location: Optional[str] = None,
    ) -> list[tuple[JobDocument, float]]:
        """
        Search for matching jobs using hybrid retrieval.
        remote_only: pushed into ChromaDB/BM25 where filter.
        location:    post-filter (ChromaDB has no substring support).
        Results are cached in Redis for 1 hour.
        """
        settings = get_settings()
        cache_key = f"search:{make_hash(f'{query}|{experience_level}|{top_k}|{remote_only}|{location}|{settings.retrieval_mode}')}"

        cached = cache_get(cache_key)
        if cached:
            logger.info(f"Search cache hit for '{query[:40]}'")
            try:
                return [
                    (JobDocument(**item["job"]), item["score"])
                    for item in cached
                ]
            except Exception as e:
                logger.warning(f"Search cache deserialise error: {e}")

        logger.info(f"Searching jobs: query='{query[:60]}', top_k={top_k}")

        # Fetch extra results when location post-filtering is needed
        fetch_k = top_k * _LOCATION_FETCH_MULTIPLIER if location else top_k
        results = retrieve_for_pipeline(
            query, top_k=fetch_k, experience_level=experience_level, remote_only=remote_only
        )

        # Location post-filter (case-insensitive substring match)
        if location:
            loc_lower = location.lower()
            results = [
                (job, score) for job, score in results
                if loc_lower in job.location.lower()
            ]
            results = results[:top_k]

        if results:
            serialisable = [
                {"job": job.model_dump(), "score": score}
                for job, score in results
            ]
            cache_set(cache_key, serialisable, ttl=settings.redis_ttl_search)

        return results

    def search_jobs_debug(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        experience_level: Optional[str] = None,
        remote_only: bool = False,
    ) -> HybridResult:
        """Debug version — returns full HybridResult with all scores. Not cached."""
        settings = get_settings()
        return hybrid_retrieve(
            query, top_k=top_k, experience_level=experience_level,
            remote_only=remote_only, mode=settings.retrieval_mode,
        )

    def search_by_skills(
        self,
        skills: list[str],
        top_k: int = DEFAULT_TOP_K,
        experience_level: Optional[str] = None,
    ) -> list[tuple[JobDocument, float]]:
        query = f"Software engineer with skills in {', '.join(skills)}"
        return self.search_jobs(query, top_k=top_k, experience_level=experience_level)

    def build_resume_query(
        self,
        skills: list[str],
        experience_level: str,
        summary: Optional[str],
    ) -> str:
        parts = []
        if summary:
            parts.append(summary[:300])
        parts.append(f"Technical skills: {', '.join(skills[:20])}")
        parts.append(f"Experience level: {experience_level}")
        return ". ".join(parts)

    def invalidate_search_cache(self) -> int:
        """
        Clear all search result caches — call this after a new ingestion run
        so users get results that include the new jobs.
        """
        deleted = cache_delete_pattern("search:*")
        logger.info(f"Search cache invalidated: {deleted} keys removed")
        return deleted


def get_retrieval_service() -> RetrievalService:
    return RetrievalService()
