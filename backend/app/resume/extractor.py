import re
from app.schemas.resume_schema import ParsedResume, Education, WorkExperience, Project
from app.utils.text_utils import extract_email, extract_phone, deduplicate_skills
from app.core.logging import get_logger

logger = get_logger(__name__)

# Common AI/software skills to look for
KNOWN_SKILLS = [
    "python", "javascript", "typescript", "java", "c++", "rust", "go",
    "fastapi", "django", "flask", "next.js", "react", "vue", "angular",
    "langchain", "langgraph", "langsmith", "llamaindex",
    "openai", "gemini", "anthropic", "huggingface",
    "sentence-transformers", "transformers",
    "chromadb", "pinecone", "weaviate", "qdrant", "faiss", "pgvector",
    "pytorch", "tensorflow", "scikit-learn", "numpy", "pandas",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
    "postgresql", "mysql", "sqlite", "mongodb", "redis",
    "rag", "llm", "llmops", "mlops", "embeddings", "vector search",
    "prompt engineering", "fine-tuning", "lora", "rlhf",
    "rest api", "graphql", "grpc", "websocket",
    "git", "github", "ci/cd", "github actions",
    "linux", "bash", "sql",
    "machine learning", "deep learning", "nlp", "computer vision",
    "agentic ai", "multi-agent", "mcp", "tool use",
    "n8n", "zapier", "airflow",
]


def extract_skills_from_text(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return deduplicate_skills(found)


def extract_name(text: str) -> str | None:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        first_line = lines[0]
        if len(first_line.split()) <= 5 and not "@" in first_line:
            return first_line
    return None


def estimate_experience_level(years: float | None, text: str) -> str:
    text_lower = text.lower()
    if years is not None:
        if years < 1:
            return "intern"
        elif years < 2:
            return "entry"
        elif years < 5:
            return "mid"
        else:
            return "senior"
    if any(w in text_lower for w in ["intern", "internship", "student"]):
        return "intern"
    if any(w in text_lower for w in ["junior", "entry", "fresher", "graduate"]):
        return "entry"
    if any(w in text_lower for w in ["senior", "lead", "staff", "principal"]):
        return "senior"
    return "entry"


def basic_extract(raw_text: str) -> ParsedResume:
    """Heuristic extraction — used when LLM extraction is unavailable."""
    skills = extract_skills_from_text(raw_text)
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    name = extract_name(raw_text)
    exp_level = estimate_experience_level(None, raw_text)

    return ParsedResume(
        raw_text=raw_text,
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        experience_level=exp_level,
    )
