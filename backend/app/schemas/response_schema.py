"""
Pydantic response envelopes — the JSON shapes the FastAPI routes return.

What it does:
- HealthResponse / ErrorResponse: generic API plumbing payloads.
- ResumeUploadResponse: wraps a ParsedResume + resume_id after PDF upload.
- JobSearchResponse: list of RankedJobs returned by /search.
- AnalysisResponse: full pipeline output (top jobs, missing skills, suggestions).

Upstream (who imports this): app.api.routes.analysis_routes, app.api.routes.search_routes,
app.api.routes.resume_routes (used as response_model on the route decorators).
Downstream (what this imports): pydantic (BaseModel, Field), typing.Optional/Any,
app.schemas.resume_schema.ParsedResume, app.schemas.job_schema.RankedJob.
"""
# BaseModel/Field: declare typed response envelopes; Field unused here but kept for future fields
from pydantic import BaseModel, Field
# Optional/Any: many response fields are nullable (parsed_resume, processing_time_ms, detail blob)
from typing import Optional, Any
# ParsedResume: nested inside ResumeUploadResponse so the client gets parse output immediately
from app.schemas.resume_schema import ParsedResume
# RankedJob: list element type for both JobSearchResponse.jobs and AnalysisResponse.top_jobs
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
    analysis_id: Optional[str] = None
    top_jobs: list[RankedJob]
    overall_match_summary: str
    top_missing_skills: list[str]
    improvement_suggestions: list[str]
    processing_time_ms: Optional[float] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None
