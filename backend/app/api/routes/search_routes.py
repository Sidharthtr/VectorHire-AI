import time
from fastapi import APIRouter, HTTPException
from app.services.retrieval_service import get_retrieval_service
from app.schemas.job_schema import JobSearchQuery, RankedJob
from app.schemas.response_schema import JobSearchResponse
from app.rag.similarity import similarity_to_percentage
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
