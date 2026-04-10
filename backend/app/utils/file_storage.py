from pathlib import Path
import uuid

from app.core.config import settings


def save_uploaded_file(file, original_filename: str) -> Path:
    """
    Saves uploaded file with UUID-based name.
    Prevents filename collisions.
    """

    storage_dir = Path(settings.FILE_STORAGE_PATH)
    storage_dir.mkdir(parents=True, exist_ok=True)

    extension = original_filename.split(".")[-1]
    stored_name = f"{uuid.uuid4()}.{extension}"

    file_path = storage_dir / stored_name

    with open(file_path, "wb") as buffer:
        buffer.write(file)

    return file_path
