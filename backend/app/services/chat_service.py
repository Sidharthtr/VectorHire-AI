"""
Chat service for follow-up questions on a saved ResumeAnalysis.

Builds a career-coach prompt grounded in analysis_json (matched jobs,
skill gaps, improvement roadmap) plus prior conversation turns, then
streams tokens from the LLM gateway.

No LangGraph — this is a lightweight conversation layer.
"""
from __future__ import annotations

from typing import Iterable

from app.llm.gateway import get_llm_gateway
from app.core.logging import get_logger

logger = get_logger(__name__)


SYSTEM_PROMPT = (
    "You are VectorHire AI's career coach. The user has uploaded a resume and "
    "received a personalized job-match analysis. Answer follow-up questions "
    "about their matched jobs, skill gaps, and improvement roadmap.\n\n"
    "Rules:\n"
    "- Ground every answer in the analysis context provided below.\n"
    "- If the user asks something unrelated to their career / job search / "
    "skills, politely steer the conversation back.\n"
    "- Be concise and concrete. Prefer bullet points and short paragraphs.\n"
    "- Never invent jobs, skills, or numbers that aren't in the analysis."
)


def _format_analysis_context(analysis_json: dict) -> str:
    """Compact, token-efficient summary of the analysis blob."""
    lines: list[str] = ["=== ANALYSIS CONTEXT ==="]

    summary = analysis_json.get("overall_match_summary")
    if summary:
        lines.append(f"\nCareer summary:\n{summary}")

    top_jobs = analysis_json.get("top_jobs") or []
    if top_jobs:
        lines.append("\nTop matched jobs:")
        for i, j in enumerate(top_jobs[:5], 1):
            job = j.get("job") or {}
            pct = j.get("match_percentage", 0)
            matched = ", ".join(j.get("matched_skills", [])[:6]) or "—"
            missing = ", ".join(j.get("missing_skills", [])[:6]) or "—"
            lines.append(
                f"{i}. {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')} "
                f"({pct:.0f}% match)\n"
                f"   Matched: {matched}\n"
                f"   Missing: {missing}"
            )

    missing = analysis_json.get("top_missing_skills") or []
    if missing:
        lines.append(f"\nTop skills to learn: {', '.join(missing[:10])}")

    suggestions = analysis_json.get("improvement_suggestions") or []
    if suggestions:
        lines.append("\nImprovement roadmap:")
        for i, s in enumerate(suggestions[:6], 1):
            lines.append(f"{i}. {s}")

    lines.append("\n=== END CONTEXT ===")
    return "\n".join(lines)


def build_messages(
    analysis_json: dict,
    history: list[dict],
    user_message: str,
) -> list[dict]:
    """Compose the message list passed to the LLM."""
    system = SYSTEM_PROMPT + "\n\n" + _format_analysis_context(analysis_json or {})
    msgs: list[dict] = [{"role": "system", "content": system}]
    # history is a list of {"role": "user"|"assistant", "content": str}
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_message})
    return msgs


def stream_reply(
    analysis_json: dict,
    history: list[dict],
    user_message: str,
) -> Iterable[str]:
    """Yield assistant content tokens for the new user message."""
    messages = build_messages(analysis_json, history, user_message)
    logger.debug(f"chat stream: {len(history)} prior turns, prompt len={sum(len(m['content']) for m in messages)}")
    gateway = get_llm_gateway()
    yield from gateway.stream_chat(messages, temperature=0.5, max_tokens=600)
