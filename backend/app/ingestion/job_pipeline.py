"""
Job ingestion pipeline — orchestrates fetch → normalise → deduplicate → embed → store.

This is the main entry point for running the ingestion:

    from app.ingestion.job_pipeline import run_ingestion
    result = run_ingestion(query="Python developer", location="remote", limit=100)

The pipeline:
0. Cleanup jobs older than TTL_DAYS (default 30 days) from ChromaDB
1. Calls every registered ingestor's fetch_jobs()
2. Normalises raw jobs into JobDocuments
3. Deduplicates by job ID (MD5 of title+company+source)
4. Embeds and stores new jobs in ChromaDB
5. Persists metadata to PostgreSQL (optional, non-blocking)
6. Returns an IngestionResult summary

Add a new source by:
1. Creating a new adapter in adapters/
2. Adding it to _get_ingestors() below
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.ingestion.base_ingestor import BaseIngestor
from app.ingestion.job_normalizer import normalise
from app.ingestion.job_embedder import embed_and_store_jobs
from app.schemas.job_schema import JobDocument
from app.core.logging import get_logger

logger = get_logger(__name__)


_TTL_DAYS = 30  # jobs older than this are deleted before each ingestion run


@dataclass
class IngestionResult:
    """Summary returned after a pipeline run."""
    total_fetched: int = 0
    total_normalised: int = 0
    total_deduplicated: int = 0
    total_stored: int = 0
    cleaned_up: int = 0          # jobs deleted because they exceeded TTL
    errors: list[str] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)


def _get_ingestors() -> list[BaseIngestor]:
    """
    Return all registered ingestors.
    Ingestors that are unavailable (missing credentials) are skipped.
    """
    from app.ingestion.adapters.adzuna_adapter import AdzunaIngestor
    from app.ingestion.adapters.arbeitnow_adapter import ArbeitnowIngestor

    candidates = [AdzunaIngestor(), ArbeitnowIngestor()]
    available = [i for i in candidates if i.is_available()]
    skipped = [i.source_name for i in candidates if not i.is_available()]
    if skipped:
        logger.info(f"Skipping unavailable ingestors: {skipped}")
    return available


def run_ingestion(
    query: str = "software engineer",
    location: str = "remote",
    limit: int = 50,
    ingestors: Optional[list[BaseIngestor]] = None,
) -> IngestionResult:
    """
    Run the full ingestion pipeline.

    Args:
        query:     job search query (e.g. "Python backend engineer")
        location:  location filter (e.g. "remote", "London", "New York")
        limit:     max jobs to fetch per source
        ingestors: override list of ingestors (default: all available)

    Returns:
        IngestionResult summary.
    """
    result = IngestionResult()
    all_ingestors = ingestors if ingestors is not None else _get_ingestors()

    if not all_ingestors:
        result.errors.append("No ingestors available — check API credentials in .env")
        logger.warning("Ingestion aborted: no ingestors available")
        return result

    # Step 0: Clean up expired jobs before fetching new ones.
    # This keeps ChromaDB lean — no stale 2-month-old listings polluting results.
    try:
        from app.rag.cleanup import cleanup_old_jobs
        cleanup = cleanup_old_jobs(days=_TTL_DAYS)
        result.cleaned_up = cleanup.deleted
        if cleanup.deleted:
            logger.info(f"TTL cleanup: removed {cleanup.deleted} jobs older than {_TTL_DAYS} days")
    except Exception as e:
        logger.warning(f"TTL cleanup failed (non-fatal): {e}")

    raw_jobs_all: list[JobDocument] = []

    # Step 1: Fetch from all sources
    for ingestor in all_ingestors:
        try:
            logger.info(f"Fetching from {ingestor.source_name}...")
            raw = ingestor.fetch_jobs(query=query, location=location, limit=limit)
            result.total_fetched += len(raw)
            result.sources_used.append(ingestor.source_name)

            # Step 2: Normalise
            for raw_job in raw:
                job = normalise(raw_job)
                if job:
                    raw_jobs_all.append(job)
                    result.total_normalised += 1

        except Exception as e:
            msg = f"{ingestor.source_name} fetch error: {e}"
            logger.error(msg)
            result.errors.append(msg)

    # Step 3: Deduplicate by ID
    seen_ids: set[str] = set()
    unique_jobs: list[JobDocument] = []
    for job in raw_jobs_all:
        if job.id not in seen_ids:
            seen_ids.add(job.id)
            unique_jobs.append(job)
    result.total_deduplicated = result.total_normalised - len(unique_jobs)

    # Step 4: Embed + store in ChromaDB
    stored = embed_and_store_jobs(unique_jobs)
    result.total_stored = stored

    # Step 5: Persist metadata to PostgreSQL (non-blocking)
    _persist_metadata(unique_jobs[:stored])

    logger.info(
        f"Ingestion complete — fetched={result.total_fetched}, "
        f"normalised={result.total_normalised}, "
        f"deduped={result.total_deduplicated}, stored={result.total_stored}"
    )
    return result


def _persist_metadata(jobs: list[JobDocument]) -> None:
    """Save job metadata to PostgreSQL. Failures are logged, not raised."""
    # Phase 2: metadata logging only — full job table in Phase 3
    logger.debug(f"Metadata persist: {len(jobs)} jobs (DB table in Phase 3)")
