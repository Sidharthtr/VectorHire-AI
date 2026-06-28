"""
Resume upload + LLM extraction + multi-tier cache (Redis -> JSON file -> LLM).

What it does:
- Hashes uploaded PDF bytes (SHA-256) and uses that as a stable cache key.
- On hit returns the cached ParsedResume; on miss runs LLM extraction with a heuristic fallback.
- Persists every processed PDF to disk under RESUMES_DIR for audit/debug.
- Same PDF -> same ParsedResume, deterministic for testing and idempotent for re-uploads.

Upstream (who imports this): app/graph/nodes/extract_skills_node.py, app/api/routes/resume_routes.py
Downstream (what this imports): resume parser+extractor, chains.run_skill_extraction_chain, ParsedResume schemas, constants, redis_client, settings
"""
from __future__ import annotations

# uuid: generates the resume_id returned to the API caller (independent of cache key)
import uuid
# hashlib: SHA-256 of file bytes is the cache key — same PDF always hits the same slot
import hashlib
# json: persists the JSON-file fallback cache when Redis isn't configured
import json
# datetime: timestamp stored alongside each cached entry for debugging cache age
from datetime import datetime
# Path: typing for the on-disk cache file path passed in from constants
from pathlib import Path

# parse_pdf_bytes: PDF -> text via pdfplumber, run only on a true cache miss
from app.resume.parser import parse_pdf_bytes
# basic_extract: regex/heuristic fallback when the LLM extraction chain fails
from app.resume.extractor import basic_extract
# run_skill_extraction_chain: builds the EXTRACT_SKILLS_PROMPT, calls LLM, parses JSON
from app.llm.chains import run_skill_extraction_chain
# Pydantic models we hydrate from the LLM dict so downstream code gets typed objects
from app.schemas.resume_schema import ParsedResume, Education, WorkExperience, Project
# RESUMES_DIR: where raw PDFs are persisted; DATA_DIR: where the JSON cache file lives
from app.core.constants import RESUMES_DIR, DATA_DIR
# get_logger: log cache hits/misses and LLM extraction failures
from app.core.logging import get_logger
# Redis primitives — cache_get/cache_set persist the ParsedResume across restarts
from app.core.redis_client import cache_get, cache_set, make_hash
# get_settings: read redis_url + TTLs so we can short-circuit Redis when not configured
from app.core.settings import get_settings

logger = get_logger(__name__)

_CACHE_FILE = DATA_DIR / "resume_cache.json"
_CACHE_MAX  = 100


class ResumeService:
    def process_upload(self, content: bytes, filename: str) -> tuple[str, ParsedResume]:
        resume_id = uuid.uuid4().hex
        cache_key = hashlib.sha256(content).hexdigest()

        # Try Redis first, then JSON file fallback
        cached = self._cache_get(cache_key)
        if cached:
            logger.info(f"Cache hit for resume {cache_key[:8]} — skipping LLM extraction")
            self._save_to_disk(content, resume_id, filename)
            return resume_id, cached

        raw_text = parse_pdf_bytes(content, filename)
        parsed = self._extract_with_llm(raw_text)
        if parsed is None:
            logger.warning("LLM extraction failed, falling back to heuristic extraction")
            parsed = basic_extract(raw_text)

        self._cache_set(cache_key, parsed)
        self._save_to_disk(content, resume_id, filename)
        logger.info(f"Processed resume {resume_id}: {len(parsed.skills)} skills found")
        return resume_id, parsed

    def _extract_with_llm(self, raw_text: str) -> ParsedResume | None:
        try:
            data = run_skill_extraction_chain(raw_text)
            if not data:
                return None
            return ParsedResume(
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
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return None

    def _save_to_disk(self, content: bytes, resume_id: str, filename: str) -> None:
        RESUMES_DIR.mkdir(parents=True, exist_ok=True)
        dest = RESUMES_DIR / f"{resume_id}_{filename}"
        dest.write_bytes(content)

    # ── Cache read: Redis → JSON file ─────────────────────────────────────────

    def _cache_get(self, key: str) -> ParsedResume | None:
        # 1. Redis
        settings = get_settings()
        if settings.redis_url:
            data = cache_get(f"resume:{key}")
            if data:
                try:
                    return ParsedResume(**data)
                except Exception as e:
                    logger.warning(f"Redis resume parse error: {e}")

        # 2. JSON file fallback
        try:
            file_cache = self._load_json_cache()
            if key in file_cache:
                return ParsedResume(**file_cache[key]["resume"])
        except Exception as e:
            logger.warning(f"JSON cache read error: {e}")

        return None

    # ── Cache write: Redis + JSON file ────────────────────────────────────────

    def _cache_set(self, key: str, parsed: ParsedResume) -> None:
        dumped = parsed.model_dump()

        # 1. Redis
        settings = get_settings()
        if settings.redis_url:
            cache_set(f"resume:{key}", dumped, ttl=settings.redis_ttl_resume)

        # 2. JSON file (always write — serves as persistent backup)
        try:
            cache = self._load_json_cache()
            cache[key] = {
                "resume": dumped,
                "cached_at": datetime.now().isoformat(),
            }
            if len(cache) > _CACHE_MAX:
                oldest = next(iter(cache))
                del cache[oldest]
            _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            _CACHE_FILE.write_text(json.dumps(cache, indent=2, default=str))
        except Exception as e:
            logger.warning(f"JSON cache write error: {e}")

    def _load_json_cache(self) -> dict:
        if _CACHE_FILE.exists():
            try:
                return json.loads(_CACHE_FILE.read_text())
            except Exception:
                return {}
        return {}


def get_resume_service() -> ResumeService:
    return ResumeService()
