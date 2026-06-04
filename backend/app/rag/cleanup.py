"""
ChromaDB TTL cleanup — removes job postings older than N days.

Why we need this:
  - Jobs ingested via Arbeitnow/Adzuna accumulate over time.
  - A job posted 2 months ago is almost certainly filled or expired.
  - Keeping stale jobs wastes vector space and pollutes search results
    (candidate matches a job that no longer exists).

How it works:
  - Every job stored via job_embedder.py has an `ingested_at` Unix timestamp
    in its ChromaDB metadata.
  - ChromaDB supports numeric `$lt` (less-than) filters on metadata.
  - We query for all jobs where ingested_at < cutoff, get their IDs, delete them.

Jobs without `ingested_at` (e.g. seeded static jobs from seed_vectordb.py)
are intentionally kept — they're your demo/baseline data.

Default TTL: 30 days. Override with the `days` parameter.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from app.rag.vectordb import get_jobs_collection
from app.rag.sparse_retriever import reset_sparse_index
from app.core.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_TTL_DAYS = 30


@dataclass
class CleanupResult:
    deleted: int
    kept: int
    cutoff_days: int


def cleanup_old_jobs(days: int = _DEFAULT_TTL_DAYS) -> CleanupResult:
    """
    Delete jobs from ChromaDB that were ingested more than `days` ago.

    Args:
        days: age threshold in days (default 30). Jobs older than this are removed.

    Returns:
        CleanupResult with counts of deleted and kept jobs.
    """
    collection = get_jobs_collection()
    total_before = collection.count()

    if total_before == 0:
        logger.info("Cleanup: ChromaDB is empty, nothing to clean")
        return CleanupResult(deleted=0, kept=0, cutoff_days=days)

    cutoff_timestamp = int(time.time()) - (days * 24 * 60 * 60)

    # Query ChromaDB for jobs older than cutoff.
    # ingested_at is stored as int — ChromaDB $lt filter works on numbers.
    try:
        old_jobs = collection.get(
            where={"ingested_at": {"$lt": cutoff_timestamp}},
            include=[],  # we only need IDs, not documents or embeddings
        )
        old_ids = old_jobs.get("ids", [])
    except Exception as e:
        # If no jobs have ingested_at at all (e.g. all are static seed jobs),
        # ChromaDB may raise an error on the where filter — handle gracefully.
        logger.info(f"Cleanup: no timestamped jobs found ({e})")
        return CleanupResult(deleted=0, kept=total_before, cutoff_days=days)

    if not old_ids:
        logger.info(f"Cleanup: no jobs older than {days} days found")
        return CleanupResult(deleted=0, kept=total_before, cutoff_days=days)

    # Delete stale jobs
    collection.delete(ids=old_ids)
    logger.info(f"Cleanup: deleted {len(old_ids)} jobs older than {days} days")

    # BM25 index is now stale — force rebuild on next query
    reset_sparse_index()

    total_after = collection.count()
    return CleanupResult(
        deleted=len(old_ids),
        kept=total_after,
        cutoff_days=days,
    )
