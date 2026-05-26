import fitz  # PyMuPDF
from pathlib import Path
from app.utils.text_utils import clean_text
from app.core.logging import get_logger

logger = get_logger(__name__)


def parse_pdf(file_path: str | Path) -> str:
    """Extract raw text from a PDF file using PyMuPDF."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    text_parts = []
    with fitz.open(str(path)) as doc:
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

    raw_text = "\n".join(text_parts)
    cleaned = clean_text(raw_text)
    logger.info(f"Parsed PDF '{path.name}': {len(cleaned)} characters")
    return cleaned


def parse_pdf_bytes(content: bytes, filename: str = "resume.pdf") -> str:
    """Extract text from PDF bytes without saving to disk."""
    text_parts = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

    raw_text = "\n".join(text_parts)
    cleaned = clean_text(raw_text)
    logger.info(f"Parsed PDF bytes '{filename}': {len(cleaned)} characters")
    return cleaned
