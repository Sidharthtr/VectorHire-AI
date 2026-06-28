"""
Workflow step 4/5 — score and sort the retrieved jobs.

What it does:
- Reads state keys: retrieved_jobs, parsed_resume.
- Writes state keys: ranked_jobs (sorted RankedJob list), processing_steps (and errors on failure).
- Delegates the weighted scoring (semantic 0.5 + skill overlap 0.3 + keyword 0.2) to RankingService. No LLM calls here.

Upstream (who imports this): app/graph/builder.py
Downstream (what this imports): WorkflowState, RankingService, logging
"""
# WorkflowState: typed access to retrieved_jobs/parsed_resume in / ranked_jobs out
from app.graph.state import WorkflowState
# RankingService: pure-Python scorer (no network) that combines the 3 ranking signals
from app.services.ranking_service import RankingService
# get_logger: trace how many jobs were ranked or whether the node was skipped
from app.core.logging import get_logger

logger = get_logger(__name__)

_ranking_service = RankingService()


def rank_jobs_node(state: WorkflowState) -> dict:
    """Node 4: Retrieved jobs → scored, sorted RankedJob list."""
    logger.info("Node: rank_jobs")
    retrieved_jobs = state.get("retrieved_jobs", [])
    parsed_resume = state.get("parsed_resume")

    if not retrieved_jobs or not parsed_resume:
        return {
            "ranked_jobs": [],
            "processing_steps": ["rank_jobs: SKIPPED — no jobs or resume"],
        }

    try:
        ranked = _ranking_service.rank_jobs(
            jobs_with_scores=retrieved_jobs,
            candidate_skills=parsed_resume.skills,
            experience_level=parsed_resume.experience_level or "entry",
            resume_text=parsed_resume.raw_text or "",  # Phase 2: for keyword signal
        )
        return {
            "ranked_jobs": ranked,
            "processing_steps": [f"rank_jobs: OK — {len(ranked)} ranked"],
        }
    except Exception as e:
        logger.error(f"rank_jobs_node error: {e}")
        return {
            "ranked_jobs": [],
            "errors": [f"rank_jobs: {str(e)}"],
            "processing_steps": ["rank_jobs: FAILED"],
        }
