from pydantic import BaseModel, Field
from typing import Optional, Any
from app.schemas.resume_schema import ParsedResume
from app.schemas.job_schema import RankedJob


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, bool]


class ResumeUploadResponse(BaseModel):
    success: bool
    message: str
    resume_id: str
    parsed_resume: Optional[ParsedResume] = None


class JobSearchResponse(BaseModel):
    success: bool
    query: str
    total_results: int
    jobs: list[RankedJob]
    processing_time_ms: Optional[float] = None


class AnalysisResponse(BaseModel):
    success: bool
    resume_id: str
    top_jobs: list[RankedJob]
    overall_match_summary: str
    top_missing_skills: list[str]
    improvement_suggestions: list[str]
    processing_time_ms: Optional[float] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None
