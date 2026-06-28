"""
Text-cleanup and lightweight extraction helpers shared across the codebase.

What it does:
- clean_text(): collapse whitespace and strip non-ASCII (used by PDF parser)
- extract_email / extract_phone: regex-based contact field extractors
- normalize_skill / deduplicate_skills: canonicalise skill strings
- truncate_text / split_into_sentences: misc text utilities

Upstream (who imports this): app/resume/parser.py, app/resume/extractor.py
Downstream (what this imports): re, typing
"""
# re: every helper here is regex-driven (whitespace, emails, phones, sentences)
import re
# Optional: extract_email / extract_phone return None when no match is found
from typing import Optional


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    return text.strip()


def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text)
    return match.group(0).strip() if match else None


def normalize_skill(skill: str) -> str:
    return skill.strip().lower().replace("-", " ").replace("_", " ")


def deduplicate_skills(skills: list[str]) -> list[str]:
    seen = set()
    result = []
    for s in skills:
        normalized = normalize_skill(s)
        if normalized not in seen:
            seen.add(normalized)
            result.append(s.strip())
    return result


def truncate_text(text: str, max_chars: int = 2000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def split_into_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]
