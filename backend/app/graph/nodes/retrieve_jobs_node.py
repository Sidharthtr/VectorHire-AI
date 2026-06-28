"""
Workflow step 3/5 — fetch candidate jobs via hybrid (semantic + BM25) retrieval.

What it does:
- Reads state keys: parsed_resume, search_query, top_k, experience_filter.
- Writes state keys: retrieved_jobs (list of (JobDocument, score)), processing_steps (and errors on failure).
- Builds a rich query from resume skills + summary + the user's optional search query before searching.

Upstream (who imports this): app/graph/builder.py
Downstream (what this imports): WorkflowState, RetrievalService, DEFAULT_TOP_K, logging
"""
# WorkflowState: typed access to parsed_resume in / retrieved_jobs out
from app.graph.state import WorkflowState
# RetrievalService: thin facade over the hybrid retriever with Redis search caching
from app.services.retrieval_service import RetrievalService
# DEFAULT_TOP_K: fallback page size when caller didn't specify top_k
from app.core.constants import DEFAULT_TOP_K
# get_logger: log query and candidate count for debugging retrieval quality
from app.core.logging import get_logger

logger = get_logger(__name__)

_retrieval_service = RetrievalService()


def retrieve_jobs_node(state: WorkflowState) -> dict:
    """
    Node 3: ParsedResume → semantically retrieved job candidates.
    Builds a rich query from skills + experience + user's search query.
    """
    logger.info("Node: retrieve_jobs")
    parsed_resume = state.get("parsed_resume")

    if not parsed_resume:
        return {
            "retrieved_jobs": [],
            "errors": ["retrieve_jobs: no parsed resume"],
            "processing_steps": ["retrieve_jobs: SKIPPED"],
        }

    try:
        user_query = state.get("search_query") or ""
        top_k = state.get("top_k", DEFAULT_TOP_K)
        experience_filter = state.get("experience_filter")

        resume_query = _retrieval_service.build_resume_query(
            skills=parsed_resume.skills,
            experience_level=parsed_resume.experience_level or "entry",
            summary=parsed_resume.summary,
        )
        combined_query = f"{user_query} {resume_query}".strip() if user_query else resume_query

        jobs = _retrieval_service.search_jobs(
            query=combined_query,
            top_k=top_k,
            experience_level=experience_filter,
        )

        return {
            "retrieved_jobs": jobs,
            "processing_steps": [f"retrieve_jobs: OK — {len(jobs)} candidates"],
        }
    except Exception as e:
        logger.error(f"retrieve_jobs_node error: {e}")
        return {
            "retrieved_jobs": [],
            "errors": [f"retrieve_jobs: {str(e)}"],
            "processing_steps": ["retrieve_jobs: FAILED"],
        }
