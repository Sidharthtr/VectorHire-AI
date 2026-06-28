"""
Filesystem helpers for resume upload handling.

What it does:
- validate_pdf(): enforce extension allowlist and max file size
- save_upload(): write uploaded bytes to disk under a uuid-prefixed filename
- list_files / ensure_dir: lightweight directory utilities used by debug routes

Upstream (who imports this): app/api/dependencies.py, app/api/routes/debug_routes.py (per core/constants header)
Downstream (what this imports): os, uuid, pathlib, typing, app.core.constants
"""
# os: kept for path-related side use even though pathlib drives most ops here
import os
# uuid: prefix uploaded filenames to avoid collisions between users
import uuid
# Path: type-safe filesystem operations for read/write/glob
from pathlib import Path
# Optional: validate_pdf returns an (ok, error_message?) tuple
from typing import Optional
# MAX_FILE_SIZE_MB / ALLOWED_EXTENSIONS: shared upload policy constants
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
