"""
LangGraph Node 4 — Rank Jobs.

Takes retrieved (JobDocument, score) pairs and produces sorted RankedJob list.

Phase 2 change: passes resume raw_text to ranking_service so the keyword
signal (20% weight) has text to match against, not just skills list.
"""
from app.graph.state import WorkflowState
from app.services.ranking_service import RankingService
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
