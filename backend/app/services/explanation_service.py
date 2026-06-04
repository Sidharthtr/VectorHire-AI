from concurrent.futures import ThreadPoolExecutor, as_completed
from app.schemas.job_schema import RankedJob
from app.schemas.resume_schema import ParsedResume
from app.llm.chains import run_explanation_chain, run_suggestions_chain, run_overall_summary_chain
from app.core.logging import get_logger
from collections import Counter

logger = get_logger(__name__)

_EXPLAIN_TOP_N = 3        # Only explain top N jobs
_MAX_WORKERS   = 3        # Parallel LLM threads


class ExplanationService:
    def explain_top_matches(self, ranked_jobs: list[RankedJob], resume: ParsedResume) -> list[RankedJob]:
        top = ranked_jobs[:_EXPLAIN_TOP_N]
        rest = ranked_jobs[_EXPLAIN_TOP_N:]

        # Run explanation calls in parallel — 3x faster than sequential
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            futures = {
                executor.submit(self._generate_explanation, job, resume): i
                for i, job in enumerate(top)
            }
            results = {}
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()

        explained = [
            top[i].model_copy(update={"explanation": results[i]})
            for i in range(len(top))
        ]
        explained.extend(rest)
        return explained

    def _generate_explanation(self, job: RankedJob, resume: ParsedResume) -> str:
        try:
            return run_explanation_chain(
                candidate_skills=resume.skills,
                experience_level=resume.experience_level or "entry",
                candidate_summary=resume.summary or "",
                job_title=job.job.title,
                job_company=job.job.company,
                matched_skills=job.matched_skills,
                missing_skills=job.missing_skills,
                similarity_score=job.similarity_score,
            )
        except Exception as e:
            logger.warning(f"Explanation failed for '{job.job.title}': {e}")
            return f"Strong alignment with {len(job.matched_skills)} matching skills including {', '.join(job.matched_skills[:3])}."

    def get_top_missing_skills(self, ranked_jobs: list[RankedJob], top_n: int = 10) -> list[str]:
        counter: Counter = Counter()
        for job in ranked_jobs:
            for skill in job.missing_skills:
                counter[skill.lower()] += 1
        return [skill for skill, _ in counter.most_common(top_n)]

    def generate_suggestions(self, resume: ParsedResume, ranked_jobs: list[RankedJob]) -> list[str]:
        missing = self.get_top_missing_skills(ranked_jobs)
        target_roles = list({j.job.title for j in ranked_jobs[:10]})
        return run_suggestions_chain(missing, resume.skills, target_roles)

    def generate_overall_summary(self, resume: ParsedResume, ranked_jobs: list[RankedJob]) -> str:
        if not ranked_jobs:
            return "No matching jobs found. Try broadening your skill set."
        scores = [j.similarity_score for j in ranked_jobs]
        return run_overall_summary_chain(
            experience_level=resume.experience_level or "entry",
            job_count=len(ranked_jobs),
            top_match=max(scores),
            avg_match=sum(scores) / len(scores),
            missing_skills=self.get_top_missing_skills(ranked_jobs),
        )


def get_explanation_service() -> ExplanationService:
    return ExplanationService()
