from app.graph.state import WorkflowState
from app.services.explanation_service import ExplanationService
from app.core.logging import get_logger

logger = get_logger(__name__)

_explanation_service = ExplanationService()


def explain_match_node(state: WorkflowState) -> dict:
    """
    Node 5: Ranked jobs → explanations, skill gap analysis, improvement suggestions.
    Terminal node of the workflow.
    """
    logger.info("Node: explain_match")
    ranked_jobs = state.get("ranked_jobs", [])
    parsed_resume = state.get("parsed_resume")

    if not ranked_jobs or not parsed_resume:
        return {
            "explained_jobs": [],
            "overall_summary": "No matching jobs found.",
            "top_missing_skills": [],
            "improvement_suggestions": [],
            "processing_steps": ["explain_match: SKIPPED"],
        }

    try:
        explained = _explanation_service.explain_top_matches(ranked_jobs, parsed_resume)
        missing = _explanation_service.get_top_missing_skills(ranked_jobs)
        suggestions = _explanation_service.generate_suggestions(parsed_resume, ranked_jobs)
        summary = _explanation_service.generate_overall_summary(parsed_resume, ranked_jobs)

        return {
            "explained_jobs": explained,
            "overall_summary": summary,
            "top_missing_skills": missing,
            "improvement_suggestions": suggestions,
            "processing_steps": [f"explain_match: OK — {len(explained)} explained"],
        }
    except Exception as e:
        logger.error(f"explain_match_node error: {e}")
        return {
            "explained_jobs": ranked_jobs,
            "overall_summary": "Analysis complete.",
            "top_missing_skills": [],
            "improvement_suggestions": [],
            "errors": [f"explain_match: {str(e)}"],
            "processing_steps": ["explain_match: PARTIAL"],
        }
