import pytest
from fastapi import HTTPException

from app.utils.validators import validate_file_size


def test_validate_file_size_within_limit():
    validate_file_size(file_size_bytes=1 * 1024 * 1024, max_mb=5)


def test_validate_file_size_exceeds_limit():
    with pytest.raises(HTTPException):
        validate_file_size(file_size_bytes=10 * 1024 * 1024, max_mb=5)
