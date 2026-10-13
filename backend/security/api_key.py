import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from src.config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str | None = Security(api_key_header)):
    if key is None or not secrets.compare_digest(key, API_KEY):
        raise HTTPException(
            status_code=401,
            detail="API-Key missing or invalid",
        )
