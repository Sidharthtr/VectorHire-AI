"""
Debug routes — dev-time visibility into retrieval and the database.

What it does:
- GET /debug/retrieval — side-by-side dense vs sparse (BM25) vs hybrid (RRF)
  results for a query; used to tune SIMILARITY_THRESHOLD and top_k
- GET /debug/db        — quick row-count smoke test on the SQL database

Upstream (who imports this): main.py mounts router under /api/v1 -> public
paths /api/v1/debug/*. Intended for developers, not end users.
Downstream (what this imports): services.retrieval_service to keep parity
with prod search, rag.hybrid_retriever for the three-mode comparison,
core.constants.DEFAULT_TOP_K for the default page size.
"""
from __future__ import annotations

# APIRouter: route group; Query: declare query-string params with validation + docs
from fastapi import APIRouter, Query
# BaseModel: declare the typed debug response payloads
from pydantic import BaseModel
# Optional: experience_level filter on the retrieval debug endpoint
from typing import Optional

# RetrievalService: instantiated once at import time so debug calls reuse the warmed index
from app.services.retrieval_service import RetrievalService
# hybrid_retrieve: lower-level retriever exposing dense/sparse/hybrid modes for side-by-side comparison
from app.rag.hybrid_retriever import hybrid_retrieve
# DEFAULT_TOP_K: shared default page size so debug matches production behavior
from app.core.constants import DEFAULT_TOP_K
# get_logger: structured logging (kept for future error paths)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["debug"])

_retrieval_service = RetrievalService()


class RetrievalDebugItem(BaseModel):
    rank: int
    job_id: str
    title: str
    company: str
    dense_score: float
    sparse_score: float
    rrf_score: float


class RetrievalDebugResponse(BaseModel):
    query: str
    mode: str
    dense_results: list[RetrievalDebugItem]
    sparse_results: list[RetrievalDebugItem]
    hybrid_results: list[RetrievalDebugItem]


@router.get("/debug/retrieval", response_model=RetrievalDebugResponse)
def debug_retrieval(
    query: str = Query(..., description="Search query to test", min_length=1),
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=20),
    experience_level: Optional[str] = Query(default=None),
):
    """
    Compare dense, sparse, and hybrid retrieval results for a query.
    Useful for understanding how BM25 and semantic search complement each other.
    """
    from app.core.settings import get_settings
    mode = get_settings().retrieval_mode

    # Run all three modes regardless of settings.retrieval_mode
    dense_result  = hybrid_retrieve(query, top_k=top_k, experience_level=experience_level, mode="dense")
    sparse_result = hybrid_retrieve(query, top_k=top_k, experience_level=experience_level, mode="sparse")
    hybrid_result = hybrid_retrieve(query, top_k=top_k, experience_level=experience_level, mode="hybrid")

    def _to_items(result, mode_override) -> list[RetrievalDebugItem]:
        items = []
        for rank, r in enumerate(result.results, 1):
            items.append(RetrievalDebugItem(
                rank=rank,
                job_id=r.job.id,
                title=r.job.title,
                company=r.job.company,
                dense_score=round(r.dense_score, 4),
                sparse_score=round(r.sparse_score, 4),
                rrf_score=round(r.rrf_score, 6),
            ))
        return items

    return RetrievalDebugResponse(
        query=query,
        mode=mode,
        dense_results=_to_items(dense_result, "dense"),
        sparse_results=_to_items(sparse_result, "sparse"),
        hybrid_results=_to_items(hybrid_result, "hybrid"),
    )


@router.get("/debug/db")
def debug_db():
    """Quick check that the SQLite database is reachable and tables exist."""
    try:
        from app.db.session import SessionLocal
        from app.db.models import Resume, Evaluation
        with SessionLocal() as db:
            resume_count = db.query(Resume).count()
            eval_count = db.query(Evaluation).count()
        return {
            "status": "ok",
            "resume_rows": resume_count,
            "evaluation_rows": eval_count,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
