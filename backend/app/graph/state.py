from typing import TypedDict, Optional, Annotated
import operator
from app.schemas.resume_schema import ParsedResume
from app.schemas.job_schema import JobDocument, RankedJob


class WorkflowState(TypedDict):
    # Input
    resume_bytes: bytes
    resume_filename: str
    search_query: Optional[str]
    top_k: int
    experience_filter: Optional[str]

    # Stage: parse_resume
    resume_id: str
    raw_text: str

    # Stage: extract_skills
    parsed_resume: Optional[ParsedResume]

    # Stage: retrieve_jobs
    retrieved_jobs: list[tuple[JobDocument, float]]

    # Stage: rank_jobs
    ranked_jobs: list[RankedJob]

    # Stage: explain_match
    explained_jobs: list[RankedJob]
    overall_summary: str
    top_missing_skills: list[str]
    improvement_suggestions: list[str]

    # Metadata
    errors: Annotated[list[str], operator.add]
    processing_steps: Annotated[list[str], operator.add]
