from app.schemas.job_schema import JobDocument, RankedJob
from app.llm.chains import run_job_ranking_chain
from app.rag.similarity import similarity_to_percentage
from app.core.logging import get_logger

logger = get_logger(__name__)


class RankingService:
    def rank_jobs(
        self,
        jobs_with_scores: list[tuple[JobDocument, float]],
        candidate_skills: list[str],
        experience_level: str,
    ) -> list[RankedJob]:
        ranked = []
        for job, similarity in jobs_with_scores:
            ranking_data = self._rank_single(job, candidate_skills, experience_level)
            matched = ranking_data.get("matched_skills", []) if ranking_data else self._simple_match(candidate_skills, job.skills)
            missing = ranking_data.get("missing_skills", []) if ranking_data else self._simple_missing(candidate_skills, job.skills)
            fit_score = ranking_data.get("fit_score", similarity_to_percentage(similarity)) if ranking_data else similarity_to_percentage(similarity)

            ranked.append(RankedJob(
                job=job,
                similarity_score=round(similarity, 4),
                match_percentage=float(fit_score),
                matched_skills=matched,
                missing_skills=missing,
            ))

        ranked.sort(key=lambda r: r.match_percentage, reverse=True)
        return ranked

    def _rank_single(self, job: JobDocument, candidate_skills: list[str], experience_level: str) -> dict | None:
        try:
            return run_job_ranking_chain(
                candidate_skills=candidate_skills,
                experience_level=experience_level,
                job_title=job.title,
                job_company=job.company,
                job_skills=job.skills,
                job_description=job.description,
            )
        except Exception as e:
            logger.warning(f"Ranking chain failed for '{job.title}': {e}")
            return None

    def _simple_match(self, candidate_skills: list[str], job_skills: list[str]) -> list[str]:
        c_lower = {s.lower() for s in candidate_skills}
        return [s for s in job_skills if s.lower() in c_lower]

    def _simple_missing(self, candidate_skills: list[str], job_skills: list[str]) -> list[str]:
        c_lower = {s.lower() for s in candidate_skills}
        return [s for s in job_skills if s.lower() not in c_lower]


def get_ranking_service() -> RankingService:
    return RankingService()
