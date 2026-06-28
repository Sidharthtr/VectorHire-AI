"""
Workflow step 5/5 — terminal node that produces user-facing explanations.

What it does:
- Reads state keys: ranked_jobs, parsed_resume.
- Writes state keys: explained_jobs, overall_summary, top_missing_skills, improvement_suggestions, processing_steps (errors on failure).
- Runs LLM calls in parallel for the top-N jobs via ExplanationService; degrades to a partial response on error.

Upstream (who imports this): app/graph/builder.py
Downstream (what this imports): WorkflowState, ExplanationService, logging
"""
# WorkflowState: typed access to ranked_jobs/parsed_resume in / explained_* out
from app.graph.state import WorkflowState
# ExplanationService: encapsulates the 4 explanation LLM chains plus a ThreadPoolExecutor for parallelism
from app.services.explanation_service import ExplanationService
# get_logger: log final step completion or partial-failure mode
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
