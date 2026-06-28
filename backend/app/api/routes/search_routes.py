"""
Search routes — semantic job search that does NOT require a resume upload.

What it does:
- POST /search/jobs       — run a free-text semantic search over ChromaDB
  with optional experience/remote/location filters; returns RankedJob[]
- GET  /search/jobs/sample — quick sanity-check endpoint returning a few jobs

Upstream (who imports this): main.py mounts router under /api/v1 -> public
paths /api/v1/search/*. Frontend search box and dev smoke-tests call these.
Downstream (what this imports): services.retrieval_service for the hybrid
(dense + BM25) retrieval, rag.similarity to translate cosine into a 0-100%,
schemas for typed query/response shapes.
"""
# time: measure processing_time_ms returned in the response
import time
# APIRouter: group /search/* routes; HTTPException: bubble 500s with detail on failure
from fastapi import APIRouter, HTTPException
# get_retrieval_service: singleton accessor for the dense/hybrid retrieval service
from app.services.retrieval_service import get_retrieval_service
# JobSearchQuery: validated request body; RankedJob: per-result wire format
from app.schemas.job_schema import JobSearchQuery, RankedJob
# JobSearchResponse: top-level response envelope (jobs + timing + count)
from app.schemas.response_schema import JobSearchResponse
# similarity_to_percentage: convert raw cosine score to a human-friendly 0-100% match
from app.rag.similarity import similarity_to_percentage
# get_logger: structured logging for search errors
from app.core.logging import get_logger

router = APIRouter(prefix="/search", tags=["Search"])
logger = get_logger(__name__)


@router.post("/jobs", response_model=JobSearchResponse)
async def search_jobs(query: JobSearchQuery):
    """Semantic job search without resume upload."""
    t_start = time.time()
    service = get_retrieval_service()

    try:
        results = service.search_jobs(
            query=query.query,
            top_k=query.top_k,
            experience_level=query.experience_level,
            remote_only=query.remote_only,
            location=query.location,
        )
        ranked = [
            RankedJob(
                job=job,
                similarity_score=round(score, 4),
                match_percentage=similarity_to_percentage(score),
                matched_skills=[],
                missing_skills=[],
            )
            for job, score in results
        ]

        elapsed_ms = (time.time() - t_start) * 1000
        return JobSearchResponse(
            success=True,
            query=query.query,
            total_results=len(ranked),
            jobs=ranked,
            processing_time_ms=round(elapsed_ms, 1),
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/sample")
async def get_sample_jobs(top_k: int = 5):
    """Return a sample of jobs from the vector DB — useful for testing."""
    service = get_retrieval_service()
    results = service.search_jobs("software engineer AI backend", top_k=top_k)
    return {
        "jobs": [
            {"id": j.id, "title": j.title, "company": j.company, "experience_level": j.experience_level}
            for j, _ in results
        ]
    }
