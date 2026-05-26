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


class RankedJob(BaseModel):
    job: JobDocument
    similarity_score: float
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: Optional[str] = None


class JobSearchQuery(BaseModel):
    query: str
    top_k: int = 10
    experience_level: Optional[str] = None
    remote_only: bool = False
