"""
PDF text extraction layer for uploaded resumes.

What it does:
- parse_pdf(): read a PDF from disk and return cleaned plain text
- parse_pdf_bytes(): same, but for in-memory uploads (FastAPI UploadFile bytes)
- Both delegate page-by-page extraction to PyMuPDF, then clean whitespace via text_utils

Upstream (who imports this): app/services/resume_service.py, app/graph/nodes/parse_resume_node.py
Downstream (what this imports): PyMuPDF (fitz), pathlib, app.utils.text_utils, app.core.logging
"""
# fitz (PyMuPDF): high-quality PDF text extraction engine
import fitz  # PyMuPDF
# Path: type-safe filesystem path handling for on-disk PDF reads
from pathlib import Path
# clean_text: collapse whitespace and strip non-ASCII before returning extracted text
from app.utils.text_utils import clean_text
# get_logger: record parse outcomes (character counts, filenames)
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
