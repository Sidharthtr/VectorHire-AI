"""
Abstract base class that every job source adapter must subclass.

What it does:
- Defines the BaseIngestor contract (source_name, fetch_jobs, is_available)
- Enables plug-and-play: pipeline iterates all registered ingestors uniformly
- Adapter step in the data flow: adapter (fetch raw) -> normalizer -> embedder -> pipeline

Upstream (who imports this): app/ingestion/job_pipeline.py, adapters/adzuna_adapter.py, adapters/arbeitnow_adapter.py
Downstream (what this imports): abc (ABC interface), app.ingestion.job_normalizer (RawJob type)
"""
from __future__ import annotations

# ABC + abstractmethod: enforce that subclasses implement fetch_jobs at class definition time
from abc import ABC, abstractmethod
# Optional: kept for type-hint compatibility in subclasses extending this interface
from typing import Optional

# RawJob: the common TypedDict every adapter must return from fetch_jobs
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
