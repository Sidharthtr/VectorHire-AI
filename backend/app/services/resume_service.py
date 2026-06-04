import uuid
import hashlib
import json
from datetime import datetime
from pathlib import Path
from app.resume.parser import parse_pdf_bytes
from app.resume.extractor import basic_extract
from app.llm.chains import run_skill_extraction_chain
from app.schemas.resume_schema import ParsedResume, Education, WorkExperience, Project
from app.core.constants import RESUMES_DIR, DATA_DIR
from app.core.logging import get_logger

logger = get_logger(__name__)

_CACHE_FILE = DATA_DIR / "resume_cache.json"
_CACHE_MAX  = 100   # max cached resumes


class ResumeService:
    def process_upload(self, content: bytes, filename: str) -> tuple[str, ParsedResume]:
        resume_id = uuid.uuid4().hex
        cache_key = hashlib.sha256(content).hexdigest()

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

    def _cache_get(self, key: str) -> ParsedResume | None:
        try:
            cache = self._load_cache()
            if key in cache:
                return ParsedResume(**cache[key]["resume"])
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None

    def _cache_set(self, key: str, parsed: ParsedResume) -> None:
        try:
            cache = self._load_cache()
            cache[key] = {
                "resume": parsed.model_dump(),
                "cached_at": datetime.now().isoformat(),
            }
            # Evict oldest entries beyond limit
            if len(cache) > _CACHE_MAX:
                oldest = next(iter(cache))
                del cache[oldest]
            _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            _CACHE_FILE.write_text(json.dumps(cache, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def _load_cache(self) -> dict:
        if _CACHE_FILE.exists():
            try:
                return json.loads(_CACHE_FILE.read_text())
            except Exception:
                return {}
        return {}


def get_resume_service() -> ResumeService:
    return ResumeService()
