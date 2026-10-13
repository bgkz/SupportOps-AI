import pytest
from fastapi import HTTPException

from backend.config import BACKEND_API_KEY
from backend.security.api_key import verify_api_key


def test_verify_api_key_valid() -> None:
    verify_api_key(key=BACKEND_API_KEY)


@pytest.mark.parametrize("key", [None, "this is not a valid api key"])
def test_verify_api_key_invalid(key: str | None) -> None:
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(key=key)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "API-Key missing or invalid"
