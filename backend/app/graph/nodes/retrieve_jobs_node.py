from app.graph.state import WorkflowState
from app.services.retrieval_service import RetrievalService
from app.core.constants import DEFAULT_TOP_K
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
