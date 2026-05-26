from fastapi import HTTPException, UploadFile
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
