from pydantic import BaseModel, Field
from typing import Optional


class JobDocument(BaseModel):
    id: str
    title: str
    company: str
    location: str
    experience_level: str  # intern, entry, mid, senior
    employment_type: str   # full-time, part-time, contract, internship
    skills: list[str]
    description: str
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    remote: bool = False
    source_file: Optional[str] = None


class ScoreBreakdown(BaseModel):
    """
    Transparent breakdown of the 3-signal match score.

    Phase 2 scoring formula:
        overall = 0.5 * semantic + 0.3 * skill_overlap + 0.2 * keyword_match

    - semantic_score:      cosine similarity from ChromaDB, converted to %
    - skill_overlap_score: % of job's required skills the candidate has
    - keyword_score:       % of job description keywords found in resume text
    - overall_score:       weighted combination (0–100)
    """
    semantic_score: float       # [0, 100]
    skill_overlap_score: float  # [0, 100]
    keyword_score: float        # [0, 100]
    overall_score: float        # [0, 100] — the final match_percentage


class RankedJob(BaseModel):
    job: JobDocument
    similarity_score: float
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: Optional[str] = None
    score_breakdown: Optional[ScoreBreakdown] = None  # Phase 2 — detailed score


class JobSearchQuery(BaseModel):
    query: str
    top_k: int = 10
    experience_level: Optional[str] = None
    remote_only: bool = False
