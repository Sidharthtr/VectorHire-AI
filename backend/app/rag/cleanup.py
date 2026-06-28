"""
ChromaDB TTL cleanup — drops jobs older than N days and invalidates BM25.

What it does:
- Uses Chroma's `$lt` numeric filter on `ingested_at` metadata to find expired jobs,
  deletes them, and calls reset_sparse_index() so BM25 rebuilds on the next query.
- Sits OUTSIDE the query path — invoked by the ingestion pipeline (and could be
  scheduled) so stale postings don't pollute retrieval results.
- Seeded/static jobs lack `ingested_at` and are intentionally preserved.

Upstream (who imports this): app/ingestion/job_pipeline.py
Downstream (what this imports): app.rag.vectordb, app.rag.sparse_retriever
"""
from __future__ import annotations

# time: produce the unix-epoch cutoff used in the $lt metadata filter
import time
# dataclass: typed return value (CleanupResult) reporting deleted / kept counts
from dataclasses import dataclass

# get_jobs_collection: target collection we query and delete from
from app.rag.vectordb import get_jobs_collection
# reset_sparse_index: BM25 corpus is now stale post-delete — force a rebuild
from app.rag.sparse_retriever import reset_sparse_index
# get_logger: reports how many jobs were removed each run
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
