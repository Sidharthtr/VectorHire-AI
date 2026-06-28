"""
Workflow step 1/5 — turn uploaded PDF bytes into raw resume text.

What it does:
- Reads state keys: resume_bytes, resume_filename.
- Writes state keys: raw_text, resume_id, processing_steps (and errors on failure).
- Isolated so it can later be swapped for a dedicated parsing agent.

Upstream (who imports this): app/graph/builder.py
Downstream (what this imports): WorkflowState, app.resume.parser, logging, uuid
"""
# WorkflowState: typed view of the shared dict so editors can autocomplete keys
from app.graph.state import WorkflowState
# parse_pdf_bytes: project's PDF -> text extractor (pdfplumber under the hood)
from app.resume.parser import parse_pdf_bytes
# get_logger: per-node logger so failures surface with a clear node name
from app.core.logging import get_logger
# uuid: assign a stable resume_id so downstream nodes / API responses can reference this run
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
