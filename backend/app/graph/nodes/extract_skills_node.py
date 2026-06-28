"""
Workflow step 2/5 — turn raw resume text into a structured ParsedResume.

What it does:
- Reads state keys: raw_text.
- Writes state keys: parsed_resume, processing_steps (and errors on failure).
- Calls the LLM extraction chain; falls back to heuristic regex extract if the LLM/JSON parse fails.

Upstream (who imports this): app/graph/builder.py
Downstream (what this imports): WorkflowState, ResumeService, basic_extract, run_skill_extraction_chain, resume schemas, logging
"""
# WorkflowState: typed access to raw_text in / parsed_resume out
from app.graph.state import WorkflowState
# ResumeService: imported for the singleton handle even though this node uses the chain directly (keeps DI symmetric)
from app.services.resume_service import ResumeService
# basic_extract: regex/heuristic fallback when the LLM extraction returns nothing usable
from app.resume.extractor import basic_extract
# run_skill_extraction_chain: builds the EXTRACT_SKILLS_PROMPT and parses the LLM's JSON reply
from app.llm.chains import run_skill_extraction_chain
# Pydantic models we hydrate from the LLM dict so the rest of the pipeline gets a typed object
from app.schemas.resume_schema import ParsedResume, Education, WorkExperience, Project
# get_logger: trace LLM successes/failures for this node
from app.core.logging import get_logger

logger = get_logger(__name__)

_resume_service = ResumeService()


def extract_skills_node(state: WorkflowState) -> dict:
    """
    Node 2: Raw text → ParsedResume with skills, experience, education.
    Uses LLM extraction with heuristic fallback.
    """
    logger.info("Node: extract_skills")
    raw_text = state.get("raw_text", "")

    if not raw_text:
        return {
            "parsed_resume": None,
            "errors": ["extract_skills: empty raw_text"],
            "processing_steps": ["extract_skills: SKIPPED"],
        }

    try:
        data = run_skill_extraction_chain(raw_text)
        if data:
            parsed = ParsedResume(
                raw_text=raw_text,
                name=data.get("name"),
                email=data.get("email"),
                phone=data.get("phone"),
                location=data.get("location"),
                summary=data.get("summary"),
                skills=data.get("skills", []),
                education=[Education(**e) for e in data.get("education", []) if isinstance(e, dict)],
                experience=[WorkExperience(**x) for x in data.get("experience", []) if isinstance(x, dict)],
                projects=[Project(**p) for p in data.get("projects", []) if isinstance(p, dict)],
                years_of_experience=data.get("years_of_experience"),
                experience_level=data.get("experience_level", "entry"),
            )
        else:
            parsed = basic_extract(raw_text)

        return {
            "parsed_resume": parsed,
            "processing_steps": [f"extract_skills: OK — {len(parsed.skills)} skills"],
        }
    except Exception as e:
        logger.error(f"extract_skills_node error: {e}")
        fallback = basic_extract(raw_text)
        return {
            "parsed_resume": fallback,
            "errors": [f"extract_skills: {str(e)}"],
            "processing_steps": ["extract_skills: FALLBACK"],
        }
