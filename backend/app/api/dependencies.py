"""
Upload validation dependency — guards routes that accept a resume PDF.

What it does:
- Provides validate_pdf_upload() to be used via Depends() on upload endpoints
- Rejects non-.pdf extensions with HTTP 400
- Rejects files larger than MAX_FILE_SIZE_MB with HTTP 413
- Rewinds the file pointer so the route handler can re-read the bytes

Upstream (who imports this): resume_routes.py — both /resume/upload and
/resume/analyze attach this as a Depends() to validate before processing.
Downstream (what this imports): core.constants.MAX_FILE_SIZE_MB and
ALLOWED_EXTENSIONS define the upload policy in one place.
"""
# HTTPException: raise typed 4xx errors on invalid uploads; UploadFile: FastAPI's streaming file wrapper
from fastapi import HTTPException, UploadFile
# MAX_FILE_SIZE_MB + ALLOWED_EXTENSIONS: policy constants compared against the incoming file
from app.core.constants import MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS


async def validate_pdf_upload(file: UploadFile) -> UploadFile:
    suffix = "." + file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only PDF files are accepted. Got: '{suffix}'")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large ({size_mb:.1f}MB). Limit: {MAX_FILE_SIZE_MB}MB")

    # Reset for downstream consumption
    await file.seek(0)
    return file
