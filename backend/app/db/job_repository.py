"""
Job registry repository — read/write helpers for the `jobs` table.

What it does:
- compute_description_hash builds an SHA-256 over title|company|description so the
  ingestion pipeline can skip re-embedding unchanged jobs.
- get_source_hashes returns existing hashes for incremental dedup per source.
- upsert inserts a new job or refreshes last_seen_at; returns (is_new, changed).
- get_stats powers the admin endpoint with per-source counts.

Upstream (who imports this): app.ingestion.job_pipeline (every ingestion run),
app.api.routes.ingestion_routes (admin stats endpoint).
Downstream (what this imports): hashlib, datetime, sqlalchemy.func, Session,
app.db.models.Job, app.schemas.job_schema.JobDocument, app.core.logging.
"""
from __future__ import annotations

# hashlib: SHA-256 over job content so we can detect description changes
import hashlib
# datetime: stamp first_seen_at / last_seen_at when upserting
from datetime import datetime

# func: SQL aggregate (count) used inside get_stats
from sqlalchemy import func
# Session: type hint for the SQLAlchemy session passed in by route/service callers
from sqlalchemy.orm import Session

# Job: the ORM model this repository reads/writes
from app.db.models import Job
# JobDocument: incoming Pydantic payload from the ingestion pipeline before persisting
from app.schemas.job_schema import JobDocument
# get_logger: module-level logger for upsert + dedup telemetry
from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_description_hash(job: JobDocument) -> str:
    content = f"{job.title}|{job.company}|{job.description}"
    return hashlib.sha256(content.encode()).hexdigest()


def get_source_hashes(db: Session, source: str) -> dict[str, str]:
    """Return {source_job_id → description_hash} for all jobs from this source."""
    rows = (
        db.query(Job.source_job_id, Job.description_hash)
        .filter(Job.source == source, Job.source_job_id.isnot(None))
        .all()
    )
    return {row.source_job_id: (row.description_hash or "") for row in rows}


def upsert(db: Session, job: JobDocument, description_hash: str) -> tuple[bool, bool]:
    """
    Upsert a job into the registry.
    Returns (is_new, description_changed).
    """
    now = datetime.utcnow()
    existing = db.query(Job).filter(Job.id == job.id).first()

    if existing:
        changed = existing.description_hash != description_hash
        existing.last_seen_at = now
        if changed:
            existing.description_hash = description_hash
        db.commit()
        return False, changed

    db.add(Job(
        id=job.id,
        source_job_id=job.source_job_id,
        source=job.source or "unknown",
        title=job.title,
        company=job.company,
        location=job.location,
        description_hash=description_hash,
        remote=job.remote,
        experience_level=job.experience_level,
        employment_type=job.employment_type,
        salary_range=job.salary_range,
        first_seen_at=now,
        last_seen_at=now,
    ))
    db.commit()
    return True, False


def get_stats(db: Session) -> dict:
    """Return aggregate stats for the admin endpoint."""
    total = db.query(func.count(Job.id)).scalar() or 0
    by_source = dict(
        db.query(Job.source, func.count(Job.id))
        .group_by(Job.source)
        .all()
    )
    return {"total_jobs": total, "by_source": by_source}
