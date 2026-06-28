"""
Orchestrates the ingestion pipeline: fetch -> normalise -> dedup -> embed -> persist.

What it does:
- TTL cleanup, multi-source fetch, ID + near-dup filtering, PG hash diff, ChromaDB embed, cache bust
- Returns an IngestionResult summary with per-stage counts and source/error lists
- Pipeline orchestrator in the data flow: adapter (fetch) -> normalizer -> embedder -> pipeline (this file)

Upstream (who imports this): app/api/routes/ingestion_routes.py
Downstream (what this imports): rapidfuzz, app.ingestion.{base_ingestor,job_normalizer,job_embedder,adapters.*}, app.schemas.job_schema, app.db.{session,job_repository}, app.rag.cleanup, app.core.{logging,redis_client}
"""
from __future__ import annotations

# dataclass/field: lightweight container for IngestionResult run statistics
from dataclasses import dataclass, field
# Optional: caller-supplied ingestor override is nullable
from typing import Optional

# fuzz: rapidfuzz token_sort_ratio for near-duplicate title+company detection
from rapidfuzz import fuzz

# BaseIngestor: typed interface for the registered source adapters
from app.ingestion.base_ingestor import BaseIngestor
# normalise: convert RawJob payloads into validated JobDocuments
from app.ingestion.job_normalizer import normalise
# embed_and_store_jobs: batch embed + ChromaDB upsert helper
from app.ingestion.job_embedder import embed_and_store_jobs
# JobDocument: canonical job record passed through the pipeline
from app.schemas.job_schema import JobDocument
# get_logger: per-stage progress and error logging
from app.core.logging import get_logger

logger = get_logger(__name__)

_TTL_DAYS = 30


@dataclass
class IngestionResult:
    """Summary returned after a pipeline run."""
    total_fetched: int = 0
    total_normalised: int = 0
    total_deduplicated: int = 0   # exact ID duplicates removed
    total_skipped: int = 0        # existing jobs with unchanged content
    total_updated: int = 0        # existing jobs re-embedded due to content change
    total_stored: int = 0         # newly embedded jobs
    cleaned_up: int = 0
    errors: list[str] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)


def _get_ingestors() -> list[BaseIngestor]:
    from app.ingestion.adapters.adzuna_adapter import AdzunaIngestor
    from app.ingestion.adapters.arbeitnow_adapter import ArbeitnowIngestor

    candidates = [AdzunaIngestor(), ArbeitnowIngestor()]
    available = [i for i in candidates if i.is_available()]
    skipped = [i.source_name for i in candidates if not i.is_available()]
    if skipped:
        logger.info(f"Skipping unavailable ingestors: {skipped}")
    return available


def _near_dup_filter(jobs: list[JobDocument]) -> tuple[list[JobDocument], int]:
    """
    Remove near-duplicates within the same source.
    Uses rapidfuzz token_sort_ratio on 'title company' strings.
    Returns (unique_jobs, n_removed).
    """
    unique: list[JobDocument] = []
    for job in jobs:
        key = f"{job.title} {job.company}".lower()
        is_dup = False
        for existing in unique:
            if existing.source != job.source:
                continue
            existing_key = f"{existing.title} {existing.company}".lower()
            if fuzz.token_sort_ratio(key, existing_key) > 95:
                is_dup = True
                break
        if not is_dup:
            unique.append(job)
    removed = len(jobs) - len(unique)
    if removed:
        logger.info(f"Near-dup filter removed {removed} jobs")
    return unique, removed


def _load_pg_hashes(sources: set[str]) -> dict[str, dict[str, str]]:
    """
    Load {source → {source_job_id → description_hash}} from PG.
    Returns empty dict on failure so the pipeline degrades gracefully.
    """
    try:
        from app.db.session import SessionLocal
        from app.db import job_repository as repo
        hashes: dict[str, dict[str, str]] = {}
        with SessionLocal() as db:
            for source in sources:
                hashes[source] = repo.get_source_hashes(db, source)
        return hashes
    except Exception as e:
        logger.warning(f"PG registry load failed (non-fatal): {e}")
        return {}


def _pg_upsert_batch(
    jobs_to_embed: list[JobDocument],
    jobs_to_touch: list[tuple[JobDocument, str]],
) -> None:
    """Upsert all processed jobs to the PG registry. Failures are non-fatal."""
    try:
        from app.db.session import SessionLocal
        from app.db import job_repository as repo
        with SessionLocal() as db:
            for job in jobs_to_embed:
                desc_hash = repo.compute_description_hash(job)
                repo.upsert(db, job, desc_hash)
            for job, desc_hash in jobs_to_touch:
                repo.upsert(db, job, desc_hash)
    except Exception as e:
        logger.warning(f"PG registry upsert failed (non-fatal): {e}")


def run_ingestion(
    query: str = "software engineer",
    location: str = "remote",
    limit: int = 50,
    ingestors: Optional[list[BaseIngestor]] = None,
) -> IngestionResult:
    result = IngestionResult()
    all_ingestors = ingestors if ingestors is not None else _get_ingestors()

    if not all_ingestors:
        result.errors.append("No ingestors available — check API credentials in .env")
        logger.warning("Ingestion aborted: no ingestors available")
        return result

    # Step 0: TTL cleanup
    try:
        from app.rag.cleanup import cleanup_old_jobs
        cleanup = cleanup_old_jobs(days=_TTL_DAYS)
        result.cleaned_up = cleanup.deleted
        if cleanup.deleted:
            logger.info(f"TTL cleanup: removed {cleanup.deleted} jobs older than {_TTL_DAYS} days")
    except Exception as e:
        logger.warning(f"TTL cleanup failed (non-fatal): {e}")

    normalised_jobs: list[JobDocument] = []

    # Steps 1 + 2: Fetch and normalise
    for ingestor in all_ingestors:
        try:
            logger.info(f"Fetching from {ingestor.source_name}...")
            raw = ingestor.fetch_jobs(query=query, location=location, limit=limit)
            result.total_fetched += len(raw)
            result.sources_used.append(ingestor.source_name)
            for raw_job in raw:
                job = normalise(raw_job)
                if job:
                    normalised_jobs.append(job)
                    result.total_normalised += 1
        except Exception as e:
            msg = f"{ingestor.source_name} fetch error: {e}"
            logger.error(msg)
            result.errors.append(msg)

    # Step 3: ID dedup — MD5(title|company|source)
    seen_ids: set[str] = set()
    id_unique: list[JobDocument] = []
    for job in normalised_jobs:
        if job.id not in seen_ids:
            seen_ids.add(job.id)
            id_unique.append(job)
    result.total_deduplicated = result.total_normalised - len(id_unique)

    # Step 4: Near-dup filter (rapidfuzz)
    unique_jobs, near_dups = _near_dup_filter(id_unique)
    result.total_deduplicated += near_dups

    # Step 5: PG registry check — classify jobs
    sources = {j.source or "unknown" for j in unique_jobs}
    pg_hashes = _load_pg_hashes(sources)

    from app.db import job_repository as repo

    jobs_to_embed: list[JobDocument] = []
    jobs_to_touch: list[tuple[JobDocument, str]] = []

    for job in unique_jobs:
        desc_hash = repo.compute_description_hash(job)
        source = job.source or "unknown"
        existing = pg_hashes.get(source, {})

        if job.source_job_id and job.source_job_id in existing:
            if existing[job.source_job_id] == desc_hash:
                result.total_skipped += 1
                jobs_to_touch.append((job, desc_hash))
            else:
                result.total_updated += 1
                jobs_to_embed.append(job)
        else:
            jobs_to_embed.append(job)

    # Step 6: Embed + store new/updated jobs
    embedded = embed_and_store_jobs(jobs_to_embed)
    result.total_stored = embedded

    # Step 7: Upsert PG registry
    _pg_upsert_batch(jobs_to_embed, jobs_to_touch)

    # Step 8: Invalidate Redis search cache
    try:
        from app.core.redis_client import cache_delete_pattern
        deleted = cache_delete_pattern("search:*")
        if deleted:
            logger.info(f"Search cache invalidated: {deleted} keys cleared")
    except Exception as e:
        logger.debug(f"Cache invalidation skipped: {e}")

    logger.info(
        f"Ingestion complete — fetched={result.total_fetched}, "
        f"normalised={result.total_normalised}, "
        f"deduped={result.total_deduplicated}, "
        f"skipped={result.total_skipped}, "
        f"updated={result.total_updated}, "
        f"stored={result.total_stored}"
    )
    return result
