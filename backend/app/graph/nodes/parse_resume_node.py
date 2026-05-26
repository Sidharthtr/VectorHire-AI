from app.graph.state import WorkflowState
from app.resume.parser import parse_pdf_bytes
from app.core.logging import get_logger
import uuid

logger = get_logger(__name__)


def parse_resume_node(state: WorkflowState) -> dict:
    """
    Node 1: Parse PDF bytes → raw text.
    Isolated so it can later become a dedicated agent.
    """
    logger.info("Node: parse_resume")
    try:
        raw_text = parse_pdf_bytes(state["resume_bytes"], state.get("resume_filename", "resume.pdf"))
        resume_id = uuid.uuid4().hex
        return {
            "raw_text": raw_text,
            "resume_id": resume_id,
            "processing_steps": ["parse_resume: OK"],
        }
    except Exception as e:
        logger.error(f"parse_resume_node error: {e}")
        return {
            "raw_text": "",
            "resume_id": uuid.uuid4().hex,
            "errors": [f"parse_resume: {str(e)}"],
            "processing_steps": ["parse_resume: FAILED"],
        }
