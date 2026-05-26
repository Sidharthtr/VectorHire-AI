import os
import uuid
from pathlib import Path
from typing import Optional
from app.core.constants import MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS


def validate_pdf(file_path: str) -> tuple[bool, Optional[str]]:
    path = Path(file_path)
    if not path.exists():
        return False, "File does not exist"
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Only {ALLOWED_EXTENSIONS} accepted"
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File size {size_mb:.1f}MB exceeds limit of {MAX_FILE_SIZE_MB}MB"
    return True, None


def save_upload(content: bytes, filename: str, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    dest_path = destination_dir / unique_name
    dest_path.write_bytes(content)
    return dest_path


def list_files(directory: Path, extension: str = ".pdf") -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob(f"*{extension}"))


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
