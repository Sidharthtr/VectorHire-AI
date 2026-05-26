from app.rag.retriever import retrieve_jobs
from app.schemas.job_schema import JobDocument
from app.core.constants import DEFAULT_TOP_K
from app.core.logging import get_logger
from typing import Optional

logger = get_logger(__name__)


class RetrievalService:
    def search_jobs(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        experience_level: Optional[str] = None,
    ) -> list[tuple[JobDocument, float]]:
        logger.info(f"Searching jobs: query='{query[:60]}', top_k={top_k}")
        return retrieve_jobs(query, top_k=top_k, experience_level=experience_level)

    def search_by_skills(
        self,
        skills: list[str],
        top_k: int = DEFAULT_TOP_K,
        experience_level: Optional[str] = None,
    ) -> list[tuple[JobDocument, float]]:
        query = f"Software engineer with skills in {', '.join(skills)}"
        return self.search_jobs(query, top_k=top_k, experience_level=experience_level)

    def build_resume_query(self, skills: list[str], experience_level: str, summary: str | None) -> str:
        parts = []
        if summary:
            parts.append(summary[:300])
        parts.append(f"Technical skills: {', '.join(skills[:20])}")
        parts.append(f"Experience level: {experience_level}")
        return ". ".join(parts)


def get_retrieval_service() -> RetrievalService:
    return RetrievalService()
