"""
Retrieval service — facade over the hybrid retriever.

LangGraph nodes call this service; the service delegates to hybrid_retriever
which runs dense (ChromaDB) + sparse (BM25) + RRF fusion based on settings.

Retrieval mode is controlled by settings.retrieval_mode:
  "dense"  → ChromaDB only (Phase 1 behaviour, fast)
  "sparse" → BM25 only (keyword-heavy searches)
  "hybrid" → Dense + Sparse + RRF (default, best results)
"""
from __future__ import annotations

from typing import Optional

from app.rag.hybrid_retriever import hybrid_retrieve, retrieve_for_pipeline, HybridResult
from app.schemas.job_schema import JobDocument
from app.core.constants import DEFAULT_TOP_K
from app.core.logging import get_logger

logger = get_logger(__name__)


class RetrievalService:
    def search_jobs(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        experience_level: Optional[str] = None,
    ) -> list[tuple[JobDocument, float]]:
        """
        Search for matching jobs using the configured retrieval mode.
        Returns (JobDocument, similarity_score) pairs for the ranking service.
        """
        logger.info(f"Searching jobs: query='{query[:60]}', top_k={top_k}")
        return retrieve_for_pipeline(query, top_k=top_k, experience_level=experience_level)

    def search_jobs_debug(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        experience_level: Optional[str] = None,
    ) -> HybridResult:
        """
        Debug version — returns full HybridResult with dense/sparse/fused scores.
        Used by the /debug/retrieval endpoint.
        """
        from app.core.settings import get_settings
        mode = get_settings().retrieval_mode
        return hybrid_retrieve(query, top_k=top_k, experience_level=experience_level, mode=mode)

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
        """Build a rich search query from resume data for better retrieval."""
        parts = []
        if summary:
            parts.append(summary[:300])
        parts.append(f"Technical skills: {', '.join(skills[:20])}")
        parts.append(f"Experience level: {experience_level}")
        return ". ".join(parts)


def get_retrieval_service() -> RetrievalService:
    return RetrievalService()
