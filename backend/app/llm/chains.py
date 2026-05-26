from app.llm.gateway import get_llm_gateway
from app.llm.prompts import (
    EXTRACT_SKILLS_PROMPT,
    RANK_JOBS_PROMPT,
    EXPLAIN_MATCH_PROMPT,
    IMPROVEMENT_SUGGESTIONS_PROMPT,
    OVERALL_SUMMARY_PROMPT,
)
from app.utils.json_utils import safe_parse_json
from app.core.logging import get_logger
from typing import Optional

logger = get_logger(__name__)


def run_skill_extraction_chain(resume_text: str) -> Optional[dict]:
    prompt = EXTRACT_SKILLS_PROMPT.format(resume_text=resume_text[:4000])
    gateway = get_llm_gateway()
    raw = gateway.complete_structured(prompt)
    parsed, err = safe_parse_json(raw)
    if err:
        logger.warning(f"Skill extraction JSON parse failed: {err}")
        return None
    return parsed


def run_job_ranking_chain(
    candidate_skills: list[str],
    experience_level: str,
    job_title: str,
    job_company: str,
    job_skills: list[str],
    job_description: str,
) -> Optional[dict]:
    prompt = RANK_JOBS_PROMPT.format(
        candidate_skills=", ".join(candidate_skills),
        experience_level=experience_level,
        job_title=job_title,
        job_company=job_company,
        job_skills=", ".join(job_skills),
        job_description=job_description[:1500],
    )
    gateway = get_llm_gateway()
    raw = gateway.complete_structured(prompt)
    parsed, err = safe_parse_json(raw)
    if err:
        logger.warning(f"Job ranking JSON parse failed: {err}")
        return None
    return parsed


def run_explanation_chain(
    candidate_skills: list[str],
    experience_level: str,
    candidate_summary: str,
    job_title: str,
    job_company: str,
    matched_skills: list[str],
    missing_skills: list[str],
    similarity_score: float,
) -> str:
    prompt = EXPLAIN_MATCH_PROMPT.format(
        candidate_skills=", ".join(candidate_skills[:20]),
        experience_level=experience_level,
        candidate_summary=candidate_summary or "Not provided",
        job_title=job_title,
        job_company=job_company,
        matched_skills=", ".join(matched_skills),
        missing_skills=", ".join(missing_skills),
        similarity_score=round(similarity_score * 100, 1),
    )
    return get_llm_gateway().complete(prompt)


def run_suggestions_chain(
    missing_skills: list[str],
    current_skills: list[str],
    target_roles: list[str],
) -> list[str]:
    prompt = IMPROVEMENT_SUGGESTIONS_PROMPT.format(
        missing_skills=", ".join(missing_skills[:15]),
        current_skills=", ".join(current_skills[:20]),
        target_roles=", ".join(target_roles[:5]),
    )
    raw = get_llm_gateway().complete_structured(prompt)
    parsed, err = safe_parse_json(raw)
    if err or not isinstance(parsed, list):
        return ["Build a RAG project with LangChain and ChromaDB",
                "Learn LangGraph for agentic workflow orchestration",
                "Practice FastAPI with async endpoints",
                "Complete a Hugging Face NLP course",
                "Deploy a model on GCP or AWS"]
    return parsed


def run_overall_summary_chain(
    experience_level: str,
    job_count: int,
    top_match: float,
    avg_match: float,
    missing_skills: list[str],
) -> str:
    prompt = OVERALL_SUMMARY_PROMPT.format(
        experience_level=experience_level,
        job_count=job_count,
        top_match=round(top_match * 100, 1),
        avg_match=round(avg_match * 100, 1),
        missing_skills=", ".join(missing_skills[:10]),
    )
    return get_llm_gateway().complete(prompt)
