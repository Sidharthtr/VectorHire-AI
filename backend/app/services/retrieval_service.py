"""
Retrieval service — facade over the hybrid retriever with Redis search caching.

Cache key: search:{hash(query + experience_level + top_k + mode)}
TTL: 1 hour (REDIS_TTL_SEARCH)

Same query from two users within an hour → second user gets instant results
from Redis, no ChromaDB or BM25 query needed.

Cache is invalidated automatically by TTL expiry, and manually via
cache_delete_pattern("search:*") after a new ingestion run.
"""
from __future__ import annotations

import json
from typing import Optional

from app.rag.hybrid_retriever import hybrid_retrieve, retrieve_for_pipeline, HybridResult
from app.schemas.job_schema import JobDocument
from app.core.constants import DEFAULT_TOP_K
from app.core.logging import get_logger
from app.core.redis_client import cache_get, cache_set, cache_delete_pattern, make_hash
from app.core.settings import get_settings

logger = get_logger(__name__)


class RetrievalService:
    def search_jobs(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        experience_level: Optional[str] = None,
    ) -> list[tuple[JobDocument, float]]:
        """
        Search for matching jobs using hybrid retrieval.
        Results are cached in Redis for 1 hour.
        """
        settings = get_settings()
        cache_key = f"search:{make_hash(f'{query}|{experience_level}|{top_k}|{settings.retrieval_mode}')}"

        # Cache hit
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

        # Cache miss — run retrieval
        logger.info(f"Searching jobs: query='{query[:60]}', top_k={top_k}")
        results = retrieve_for_pipeline(query, top_k=top_k, experience_level=experience_level)

        # Store in Redis
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
    ) -> HybridResult:
        """Debug version — returns full HybridResult with all scores. Not cached."""
        settings = get_settings()
        return hybrid_retrieve(
            query, top_k=top_k, experience_level=experience_level, mode=settings.retrieval_mode
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
