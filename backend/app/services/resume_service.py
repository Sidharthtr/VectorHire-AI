import uuid
from pathlib import Path
from app.resume.parser import parse_pdf_bytes
from app.resume.extractor import basic_extract
from app.llm.chains import run_skill_extraction_chain
from app.schemas.resume_schema import ParsedResume, Education, WorkExperience, Project
from app.core.constants import RESUMES_DIR
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResumeService:
    def process_upload(self, content: bytes, filename: str) -> tuple[str, ParsedResume]:
        resume_id = uuid.uuid4().hex
        raw_text = parse_pdf_bytes(content, filename)

        parsed = self._extract_with_llm(raw_text)
        if parsed is None:
            logger.warning("LLM extraction failed, falling back to heuristic extraction")
            parsed = basic_extract(raw_text)

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


def get_resume_service() -> ResumeService:
    return ResumeService()
