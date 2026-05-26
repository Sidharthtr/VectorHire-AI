from langgraph.graph import StateGraph
from app.graph.builder import build_workflow
from app.graph.state import WorkflowState
from app.core.constants import WORKFLOW_RECURSION_LIMIT
from app.core.logging import get_logger
from typing import Optional

logger = get_logger(__name__)

_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_workflow()
        _compiled_graph = graph.compile()
        logger.info("LangGraph workflow compiled")
    return _compiled_graph


async def run_analysis_workflow(
    resume_bytes: bytes,
    resume_filename: str,
    search_query: Optional[str] = None,
    top_k: int = 10,
    experience_filter: Optional[str] = None,
) -> WorkflowState:
    """
    Entry point for the full VectorHire analysis pipeline.
    Runs the LangGraph workflow end-to-end.
    """
    initial_state: WorkflowState = {
        "resume_bytes": resume_bytes,
        "resume_filename": resume_filename,
        "search_query": search_query,
        "top_k": top_k,
        "experience_filter": experience_filter,
        "resume_id": "",
        "raw_text": "",
        "parsed_resume": None,
        "retrieved_jobs": [],
        "ranked_jobs": [],
        "explained_jobs": [],
        "overall_summary": "",
        "top_missing_skills": [],
        "improvement_suggestions": [],
        "errors": [],
        "processing_steps": [],
    }

    app = get_compiled_graph()
    config = {"recursion_limit": WORKFLOW_RECURSION_LIMIT}

    logger.info(f"Starting workflow for '{resume_filename}'")
    final_state = await app.ainvoke(initial_state, config=config)
    logger.info(f"Workflow complete. Steps: {final_state.get('processing_steps', [])}")
    if final_state.get("errors"):
        logger.warning(f"Workflow errors: {final_state['errors']}")

    return final_state
