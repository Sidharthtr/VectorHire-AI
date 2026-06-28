"""
Typed dict that flows through every LangGraph node — the workflow's shared memory.

What it does:
- Declares every key a node may read or write across the 5-step pipeline.
- Uses operator.add (via Annotated) so 'errors' and 'processing_steps' append across nodes instead of being overwritten.

Upstream (who imports this): app/graph/builder.py, app/graph/workflow.py, every node in app/graph/nodes/
Downstream (what this imports): typing, operator, app.schemas (ParsedResume, JobDocument, RankedJob)
"""
# TypedDict: structural schema for the shared LangGraph state; Optional/Annotated: mark nullable fields and attach reducers
from typing import TypedDict, Optional, Annotated
# operator.add: used as a reducer so list fields accumulate across nodes instead of clobbering each other
import operator
# ParsedResume: shape produced by extract_skills_node and consumed downstream
from app.schemas.resume_schema import ParsedResume
# JobDocument + RankedJob: retrieval emits JobDocuments with scores; ranking emits RankedJobs
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
