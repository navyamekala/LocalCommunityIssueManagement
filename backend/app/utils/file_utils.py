"""
File Upload and Image Validation Utilities.
"""

import os
import uuid
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


def save_upload_image(file: UploadFile, upload_dir: str) -> str:
    """
    Validates and saves an uploaded image file to the upload directory.
    Returns the relative URL/path for the saved image.
    """
    if not file or not file.filename:
        return ""

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename to avoid collision
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(upload_dir, exist_ok=True)
    destination = os.path.join(upload_dir, unique_filename)

    file_content = file.file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds maximum allowed limit of 10 MB."
        )

    with open(destination, "wb") as buffer:
        buffer.write(file_content)

    return f"/uploads/{unique_filename}"
