"""
Base ingestor interface.

Every job source (Adzuna, Arbeitnow, LinkedIn, etc.) implements this
abstract class. This gives us a plug-and-play design:

    class AdzunaIngestor(BaseIngestor):
        def fetch_jobs(self, query, location, limit):
            ...  # call Adzuna API

    class ArbeitnowIngestor(BaseIngestor):
        def fetch_jobs(self, query, location, limit):
            ...  # call Arbeitnow API

The pipeline (job_pipeline.py) iterates over all registered ingestors,
calls fetch_jobs() on each, normalises, deduplicates, embeds, and stores.

Adding a new source = implementing fetch_jobs() + registering in ALL_INGESTORS.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.ingestion.job_normalizer import RawJob


class BaseIngestor(ABC):
    """Abstract base class for all job data source adapters."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name shown in logs and stored in DB."""
        ...

    @abstractmethod
    def fetch_jobs(
        self,
        query: str,
        location: str = "remote",
        limit: int = 50,
    ) -> list[RawJob]:
        """
        Fetch raw job listings from the source.

        Args:
            query:    job title or skill keywords (e.g. "Python developer")
            location: location filter (e.g. "London", "remote", "US")
            limit:    max jobs to return per call

        Returns:
            list of RawJob dicts. The normalizer will clean these up.
        """
        ...

    def is_available(self) -> bool:
        """
        Return False if required API credentials are missing.
        The pipeline skips unavailable ingestors gracefully.
        """
        return True
