"""
Hybrid retriever — orchestrates dense + sparse + RRF fusion.

This is the main entry point for retrieval in Phase 2+.
Retrieval mode is controlled by settings.retrieval_mode:
  "dense"  → ChromaDB cosine similarity only (Phase 1 behaviour)
  "sparse" → BM25 keyword search only
  "hybrid" → Dense + Sparse + RRF fusion (default, best results)

Returns HybridResult which carries per-system scores for transparency
and for the /debug/retrieval comparison endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.rag.dense_retriever import dense_retrieve
from app.rag.sparse_retriever import sparse_retrieve
from app.rag.rrf import reciprocal_rank_fusion
from app.schemas.job_schema import JobDocument
from app.core.constants import DEFAULT_TOP_K
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedJob:
    """A job with all retrieval scores attached."""
    job: JobDocument
    dense_score: float = 0.0    # Cosine similarity [0, 1]
    sparse_score: float = 0.0   # Normalised BM25 score [0, 1]
    rrf_score: float = 0.0      # RRF fusion score (sum of 1/(k+rank) terms)

    # Convenience alias used downstream by ranking_service
    @property
    def similarity(self) -> float:
        """Primary score used for semantic weighting in ranking."""
        return self.dense_score if self.dense_score > 0 else self.sparse_score


@dataclass
class HybridResult:
    """Full retrieval output carrying results from all three systems."""
    results: list[RetrievedJob] = field(default_factory=list)
    dense_results: list[tuple[JobDocument, float, int]] = field(default_factory=list)
    sparse_results: list[tuple[JobDocument, float, int]] = field(default_factory=list)
    mode_used: str = "hybrid"


def hybrid_retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    experience_level: Optional[str] = None,
    remote_only: bool = False,
    mode: str = "hybrid",
) -> HybridResult:
    """
    Main retrieval function.

    Args:
        query:            search query string
        top_k:            max results to return
        experience_level: optional filter ("entry", "mid", "senior", etc.)
        remote_only:      if True, only return remote jobs
        mode:             "dense" | "sparse" | "hybrid"

    Returns:
        HybridResult with ranked jobs and per-system scores.
    """
    dense_hits: list[tuple[JobDocument, float, int]] = []
    sparse_hits: list[tuple[JobDocument, float, int]] = []

    if mode in ("dense", "hybrid"):
        dense_hits = dense_retrieve(
            query, top_k=top_k, experience_level=experience_level, remote_only=remote_only
        )
        logger.debug(f"Dense: {len(dense_hits)} hits")

    if mode in ("sparse", "hybrid"):
        sparse_hits = sparse_retrieve(
            query, top_k=top_k, experience_level=experience_level, remote_only=remote_only
        )
        logger.debug(f"Sparse: {len(sparse_hits)} hits")

    # Build final ranked list
    if mode == "dense":
        results = [
            RetrievedJob(job=job, dense_score=score, sparse_score=0.0, rrf_score=score)
            for job, score, _ in dense_hits
        ]
    elif mode == "sparse":
        results = [
            RetrievedJob(job=job, dense_score=0.0, sparse_score=score, rrf_score=score)
            for job, score, _ in sparse_hits
        ]
    else:
        # Hybrid: fuse with RRF
        fused = reciprocal_rank_fusion(dense_hits, sparse_hits, top_k=top_k)
        results = [
            RetrievedJob(job=job, dense_score=d_score, sparse_score=s_score, rrf_score=rrf)
            for job, d_score, s_score, rrf in fused
        ]

    logger.info(f"Hybrid retrieve [{mode}]: {len(results)} results for '{query[:60]}'")
    return HybridResult(
        results=results,
        dense_results=dense_hits,
        sparse_results=sparse_hits,
        mode_used=mode,
    )


def retrieve_for_pipeline(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    experience_level: Optional[str] = None,
    remote_only: bool = False,
) -> list[tuple[JobDocument, float]]:
    """
    Convenience wrapper for LangGraph nodes — returns (JobDocument, similarity_score) pairs
    exactly like the original retriever.retrieve_jobs() did, so existing nodes need no changes.
    """
    from app.core.settings import get_settings
    mode = get_settings().retrieval_mode

    result = hybrid_retrieve(
        query, top_k=top_k, experience_level=experience_level,
        remote_only=remote_only, mode=mode,
    )
    return [(r.job, r.similarity) for r in result.results]
