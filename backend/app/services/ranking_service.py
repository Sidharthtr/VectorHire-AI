"""
Ranking service — converts retrieved jobs into scored, sorted RankedJob results.

Phase 2 scoring formula (3-signal weighted):
    overall = 0.5 * semantic_pct
            + 0.3 * skill_overlap_pct
            + 0.2 * keyword_match_pct

Weights rationale:
  - Semantic (0.5): embedding similarity captures role/domain fit holistically.
  - Skill overlap (0.3): explicit skill match is the recruiter's first filter.
  - Keyword match (0.2): BM25-style term match catches literal skill names
                          that embeddings sometimes group too broadly.

No LLM calls here — pure Python math. Keeps ranking sub-millisecond.
"""
from __future__ import annotations

import re
from app.schemas.job_schema import JobDocument, RankedJob, ScoreBreakdown
from app.rag.similarity import similarity_to_percentage
from app.core.logging import get_logger

logger = get_logger(__name__)

# Score weights — must sum to 1.0
_W_SEMANTIC  = 0.5
_W_SKILLS    = 0.3
_W_KEYWORD   = 0.2


class RankingService:
    def rank_jobs(
        self,
        jobs_with_scores: list[tuple[JobDocument, float]],
        candidate_skills: list[str],
        experience_level: str,
        resume_text: str = "",
    ) -> list[RankedJob]:
        """
        Score and sort retrieved jobs.

        Args:
            jobs_with_scores: list of (JobDocument, cosine_similarity) from retrieval
            candidate_skills: skills extracted from the resume
            experience_level: candidate's experience level (used for future filtering)
            resume_text:      raw resume text for keyword matching (optional)

        Returns:
            list of RankedJob sorted by overall score descending.
        """
        ranked = []
        for job, similarity in jobs_with_scores:
            matched = self._skill_match(candidate_skills, job.skills)
            missing = self._skill_missing(candidate_skills, job.skills)
            breakdown = self._compute_scores(
                similarity, matched, job.skills, candidate_skills, resume_text, job.description
            )

            ranked.append(RankedJob(
                job=job,
                similarity_score=round(similarity, 4),
                match_percentage=round(breakdown.overall_score, 1),
                matched_skills=matched,
                missing_skills=missing,
                score_breakdown=breakdown,
            ))

        ranked.sort(key=lambda r: r.match_percentage, reverse=True)
        return ranked

    def _compute_scores(
        self,
        similarity: float,
        matched_skills: list[str],
        job_skills: list[str],
        candidate_skills: list[str],
        resume_text: str,
        job_description: str,
    ) -> ScoreBreakdown:
        """Calculate all three signal scores and combine them."""
        # Signal 1: semantic — cosine similarity converted to 0-100%
        semantic_pct = similarity_to_percentage(similarity)

        # Signal 2: skill overlap — what % of job's required skills the candidate has
        skill_overlap_pct = (len(matched_skills) / max(len(job_skills), 1)) * 100

        # Signal 3: keyword match — what % of key job description terms appear in resume
        keyword_pct = self._keyword_match(resume_text, job_description, candidate_skills)

        overall = (
            _W_SEMANTIC  * semantic_pct
            + _W_SKILLS  * skill_overlap_pct
            + _W_KEYWORD * keyword_pct
        )

        return ScoreBreakdown(
            semantic_score=round(semantic_pct, 1),
            skill_overlap_score=round(skill_overlap_pct, 1),
            keyword_score=round(keyword_pct, 1),
            overall_score=round(overall, 1),
        )

    def _keyword_match(
        self,
        resume_text: str,
        job_description: str,
        candidate_skills: list[str],
    ) -> float:
        """
        Measure what % of significant keywords in the job description appear
        in the candidate's resume text (or skills list as a fallback).

        We extract words longer than 4 characters from the job description
        (to exclude noise words like "the", "with", "have") and check how
        many appear in the resume.
        """
        if not resume_text and not candidate_skills:
            return 0.0

        # Build search corpus: resume text + skills joined
        search_corpus = (resume_text + " " + " ".join(candidate_skills)).lower()

        # Extract meaningful keywords from job description
        words = re.findall(r"\b[a-z][a-z0-9\+\#\.]+\b", job_description.lower())
        # Filter out short/common words
        stopwords = {"with", "and", "the", "for", "are", "you", "will", "have",
                     "from", "that", "this", "our", "your", "team", "role", "work"}
        keywords = [w for w in words if len(w) > 4 and w not in stopwords]

        if not keywords:
            return 50.0  # neutral if no keywords to extract

        matched = sum(1 for kw in keywords if kw in search_corpus)
        return (matched / len(keywords)) * 100

    def _skill_match(self, candidate_skills: list[str], job_skills: list[str]) -> list[str]:
        c_lower = {s.lower() for s in candidate_skills}
        return [s for s in job_skills if s.lower() in c_lower]

    def _skill_missing(self, candidate_skills: list[str], job_skills: list[str]) -> list[str]:
        c_lower = {s.lower() for s in candidate_skills}
        return [s for s in job_skills if s.lower() not in c_lower]


def get_ranking_service() -> RankingService:
    return RankingService()
