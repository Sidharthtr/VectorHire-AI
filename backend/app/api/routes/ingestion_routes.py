"""
Job ingestion routes — trigger real job data ingestion from external APIs.

POST /api/v1/ingest
  Fetch jobs from Adzuna/Arbeitnow, embed, and store in ChromaDB.
  Returns an IngestionResult summary.

GET /api/v1/admin/stats
  Return aggregate stats from the PostgreSQL job registry.

This endpoint is for admin/developer use.
In production this would be a scheduled background task (cron every 6 hours).
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from app.ingestion.job_pipeline import run_ingestion, IngestionResult
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["ingestion"])


class IngestRequest(BaseModel):
    query: str = Field(default="software engineer", description="Job search query")
    location: str = Field(default="remote", description="Location filter")
    limit: int = Field(default=50, ge=1, le=200, description="Max jobs per source")


class IngestResponse(BaseModel):
    cleaned_up: int
    total_fetched: int
    total_normalised: int
    total_deduplicated: int
    total_skipped: int
    total_updated: int
    total_stored: int
    sources_used: list[str]
    errors: list[str]


@router.post("/ingest", response_model=IngestResponse)
def trigger_ingestion(request: IngestRequest = IngestRequest()):
    """
    Fetch real job listings from external APIs and store in ChromaDB.
    Requires ADZUNA_APP_ID / ADZUNA_API_KEY in .env for Adzuna.
    Arbeitnow needs no credentials and will always run.
    """
    logger.info(f"Ingestion triggered: query='{request.query}', location='{request.location}'")
    result: IngestionResult = run_ingestion(
        query=request.query,
        location=request.location,
        limit=request.limit,
    )
    return IngestResponse(
        cleaned_up=result.cleaned_up,
        total_fetched=result.total_fetched,
        total_normalised=result.total_normalised,
        total_deduplicated=result.total_deduplicated,
        total_skipped=result.total_skipped,
        total_updated=result.total_updated,
        total_stored=result.total_stored,
        sources_used=result.sources_used,
        errors=result.errors,
    )


@router.get("/admin/stats")
def get_ingestion_stats():
    """
    Return aggregate stats from the PostgreSQL job registry.
    Shows total jobs stored by source and ChromaDB collection count.
    """
    stats: dict = {}

    try:
        from app.db.session import SessionLocal
        from app.db import job_repository as repo
        with SessionLocal() as db:
            stats.update(repo.get_stats(db))
    except Exception as e:
        stats["pg_error"] = str(e)

    try:
        from app.rag.vectordb import get_jobs_collection
        collection = get_jobs_collection()
        stats["chromadb_count"] = collection.count()
    except Exception as e:
        stats["chromadb_error"] = str(e)

    return stats
