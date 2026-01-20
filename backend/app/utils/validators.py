from fastapi import HTTPException


def validate_file_size(file_size_bytes: int, max_mb: int):
    if file_size_bytes > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds allowed limit",
        )
