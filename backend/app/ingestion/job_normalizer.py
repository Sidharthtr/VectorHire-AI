"""
Job normalizer — converts raw API responses into clean JobDocument objects.

Different job APIs return wildly different field names and formats.
This module defines a RawJob TypedDict (the common intermediate format)
and a normalizer that converts it to our internal JobDocument schema.

Flow:
    Adzuna response dict
         ↓
    AdzunaAdapter.fetch_jobs() → RawJob  (adapter maps API fields → RawJob)
         ↓
    normalise(raw_job) → JobDocument     (normalizer cleans + validates)
         ↓
    JobEmbedder → ChromaDB + PostgreSQL
"""
from __future__ import annotations

import hashlib
import re
from typing import TypedDict, Optional

from app.schemas.job_schema import JobDocument
from app.core.logging import get_logger

logger = get_logger(__name__)

# Common tech skills for keyword extraction when an API doesn't provide them
_SKILL_PATTERNS = [
    "python", "javascript", "typescript", "java", "golang", "go", "rust", "c\\+\\+",
    "react", "next\\.?js", "vue", "angular", "node\\.?js", "fastapi", "django", "flask",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "terraform", "aws", "gcp", "azure",
    "machine learning", "deep learning", "nlp", "llm", "langchain", "pytorch", "tensorflow",
    "sql", "git", "linux", "bash",
]
_SKILL_RE = re.compile(r"\b(" + "|".join(_SKILL_PATTERNS) + r")\b", re.IGNORECASE)


class RawJob(TypedDict, total=False):
    """
    Intermediate format all adapters must produce.
    All fields optional — normalizer handles missing values gracefully.
    """
    source_job_id: str          # API's own ID (Adzuna job ID, Arbeitnow slug)
    title: str
    company: str
    location: str
    description: str
    url: str
    salary_min: Optional[float]
    salary_max: Optional[float]
    skills: list[str]           # adapter can provide these directly
    remote: bool
    employment_type: str        # full-time, part-time, contract, internship
    experience_level: str       # intern, entry, mid, senior
    source: str                 # which ingestor produced this


def normalise(raw: RawJob) -> Optional[JobDocument]:
    """
    Convert a RawJob dict into a validated JobDocument.
    Returns None if the job is clearly invalid (no title or description).
    """
    title = _clean(raw.get("title", ""))
    description = _clean(raw.get("description", ""))

    if not title or not description:
        logger.debug(f"Skipping job with no title/description: {raw.get('url', 'unknown')}")
        return None

    # Derive skills from description if the adapter didn't provide them
    skills = raw.get("skills") or _extract_skills(description)

    # Build a stable deterministic ID from title + company + source
    company = _clean(raw.get("company", "Unknown"))
    source = raw.get("source", "unknown")
    id_seed = f"{title}|{company}|{source}".lower()
    job_id = hashlib.md5(id_seed.encode()).hexdigest()[:16]

    salary_str = _format_salary(raw.get("salary_min"), raw.get("salary_max"))

    return JobDocument(
        id=job_id,
        source_job_id=raw.get("source_job_id") or None,
        source=source,
        title=title,
        company=company,
        location=_clean(raw.get("location", "Remote")),
        experience_level=_normalise_experience(raw.get("experience_level", ""), description),
        employment_type=_normalise_employment(raw.get("employment_type", "full-time")),
        skills=skills,
        description=description,
        remote=bool(raw.get("remote", False)) or "remote" in description.lower(),
        salary_range=salary_str,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Strip HTML tags and excess whitespace."""
    text = re.sub(r"<[^>]+>", " ", str(text))  # strip HTML
    return " ".join(text.split())


def _extract_skills(description: str) -> list[str]:
    """Pull tech skill keywords from a job description."""
    found = _SKILL_RE.findall(description)
    seen: set[str] = set()
    unique: list[str] = []
    for s in found:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique[:20]  # cap to avoid noisy skill lists


def _normalise_experience(raw: str, description: str) -> str:
    raw_lower = (raw + " " + description[:300]).lower()
    if any(k in raw_lower for k in ["intern", "internship", "trainee"]):
        return "intern"
    if any(k in raw_lower for k in ["senior", "staff", "principal", "lead", "sr."]):
        return "senior"
    if any(k in raw_lower for k in ["mid", "intermediate", "2+ year", "3+ year"]):
        return "mid"
    return "entry"


def _normalise_employment(raw: str) -> str:
    raw_lower = raw.lower()
    if "contract" in raw_lower or "freelance" in raw_lower:
        return "contract"
    if "part" in raw_lower:
        return "part-time"
    if "intern" in raw_lower:
        return "internship"
    return "full-time"


def _format_salary(salary_min: Optional[float], salary_max: Optional[float]) -> Optional[str]:
    if salary_min and salary_max:
        return f"${int(salary_min):,} – ${int(salary_max):,}"
    if salary_min:
        return f"${int(salary_min):,}+"
    if salary_max:
        return f"Up to ${int(salary_max):,}"
    return None
