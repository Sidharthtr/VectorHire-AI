"""
Adzuna job board adapter.

Adzuna has a free tier API with 250 requests/day.
Register at: https://developer.adzuna.com

Required env vars (set in backend/app/.env):
    ADZUNA_APP_ID=your_app_id
    ADZUNA_API_KEY=your_api_key

If credentials are missing, is_available() returns False and the
pipeline skips this source gracefully.

API docs: https://api.adzuna.com/v1/api/jobs/{country}/search/1
"""
from __future__ import annotations

import httpx

from app.ingestion.base_ingestor import BaseIngestor
from app.ingestion.job_normalizer import RawJob
from app.core.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_BASE_URL = "https://api.adzuna.com/v1/api/jobs"
_COUNTRY  = "gb"   # "gb" = UK, "us" = USA — change as needed


class AdzunaIngestor(BaseIngestor):
    """Fetches jobs from the Adzuna job board API."""

    @property
    def source_name(self) -> str:
        return "adzuna"

    def is_available(self) -> bool:
        s = get_settings()
        return bool(s.adzuna_app_id and s.adzuna_api_key)

    def fetch_jobs(
        self,
        query: str,
        location: str = "remote",
        limit: int = 50,
    ) -> list[RawJob]:
        settings = get_settings()
        results_per_page = min(limit, 50)  # Adzuna max 50 per page
        url = f"{_BASE_URL}/{_COUNTRY}/search/1"

        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_api_key,
            "what": query,
            "where": location,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        }

        try:
            # verify=False: Zscaler corporate proxy — update for production
            with httpx.Client(verify=False, timeout=15) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Adzuna API error: {e}")
            return []

        raw_jobs: list[RawJob] = []
        for item in data.get("results", []):
            raw_jobs.append(RawJob(
                source_job_id=str(item.get("id", "")),
                title=item.get("title", ""),
                company=item.get("company", {}).get("display_name", "Unknown"),
                location=item.get("location", {}).get("display_name", location),
                description=item.get("description", ""),
                url=item.get("redirect_url", ""),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                skills=[],
                remote="remote" in item.get("description", "").lower(),
                employment_type="full-time",
                experience_level="",
                source=self.source_name,
            ))

        logger.info(f"Adzuna: fetched {len(raw_jobs)} jobs for '{query}'")
        return raw_jobs
