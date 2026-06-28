"""
Arbeitnow API adapter — fetches free tech/remote jobs (no auth required).

What it does:
- Implements BaseIngestor for Arbeitnow's public job board API
- Client-side keyword filtering (API has weak server-side search) and maps responses to RawJob
- Adapter step in the data flow: adapter (this file, fetch raw) -> normalizer -> embedder -> pipeline

Upstream (who imports this): app/ingestion/job_pipeline.py (lazy import inside _get_ingestors)
Downstream (what this imports): httpx, app.ingestion.base_ingestor, app.ingestion.job_normalizer, app.core.logging
"""
from __future__ import annotations

# httpx: sync HTTP client used to call Arbeitnow's public REST endpoint
import httpx

# BaseIngestor: parent interface this adapter implements
from app.ingestion.base_ingestor import BaseIngestor
# RawJob: intermediate dict shape the normalizer expects from every adapter
from app.ingestion.job_normalizer import RawJob
# get_logger: log fetch counts and API errors
from app.core.logging import get_logger

logger = get_logger(__name__)

_API_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowIngestor(BaseIngestor):
    """Fetches tech/remote jobs from Arbeitnow (free, no auth required)."""

    @property
    def source_name(self) -> str:
        return "arbeitnow"

    def is_available(self) -> bool:
        return True  # No API key needed

    def fetch_jobs(
        self,
        query: str,
        location: str = "remote",
        limit: int = 50,
    ) -> list[RawJob]:
        """
        Fetch jobs from Arbeitnow.
        The API returns paginated results; we fetch page 1 only (up to 50 jobs).
        Filtering by query is done client-side since the API has limited search.
        """
        try:
            # verify=False: Zscaler corporate proxy — update for production
            with httpx.Client(verify=False, timeout=15) as client:
                response = client.get(_API_URL, params={"page": 1})
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Arbeitnow API error: {e}")
            return []

        # Client-side keyword filter — keep jobs where query words appear in title or description
        query_words = query.lower().split()
        raw_jobs: list[RawJob] = []

        for item in data.get("data", []):
            title = item.get("title", "").lower()
            description = item.get("description", "").lower()
            text = title + " " + description

            # Basic relevance filter: at least one query word must match
            if not any(w in text for w in query_words):
                continue

            tags = item.get("tags", [])  # Arbeitnow returns skill tags

            raw_jobs.append(RawJob(
                source_job_id=item.get("slug", ""),
                title=item.get("title", ""),
                company=item.get("company_name", "Unknown"),
                location=item.get("location", "Remote"),
                description=item.get("description", ""),
                url=item.get("url", ""),
                salary_min=None,
                salary_max=None,
                skills=tags,          # Use Arbeitnow tags directly as skills
                remote=item.get("remote", True),
                employment_type=_map_employment(item.get("job_types", [])),
                experience_level="",
                source=self.source_name,
            ))

            if len(raw_jobs) >= limit:
                break

        logger.info(f"Arbeitnow: fetched {len(raw_jobs)} jobs for '{query}'")
        return raw_jobs


def _map_employment(job_types: list[str]) -> str:
    if not job_types:
        return "full-time"
    t = " ".join(job_types).lower()
    if "contract" in t:
        return "contract"
    if "part" in t:
        return "part-time"
    if "intern" in t:
        return "internship"
    return "full-time"
