"""
Job ingestion routes — trigger real job data ingestion from external APIs.

POST /api/v1/ingest
  Fetch jobs from Adzuna/Arbeitnow, embed, and store in ChromaDB.
  Returns an IngestionResult summary.

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
    cleaned_up: int         # jobs deleted because they were older than 30 days
    total_fetched: int
    total_normalised: int
    total_deduplicated: int
    total_stored: int
    sources_used: list[str]
    errors: list[str]


@router.post("/ingest", response_model=IngestResponse)
def trigger_ingestion(request: IngestRequest):
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
        total_stored=result.total_stored,
        sources_used=result.sources_used,
        errors=result.errors,
    )
