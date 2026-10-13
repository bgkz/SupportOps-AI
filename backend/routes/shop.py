from fastapi import APIRouter, Depends

from backend.security.api_key import verify_api_key

router = APIRouter(
    prefix="/tickets",
    dependencies=[Depends(verify_api_key)],
)
