from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from backend.dependencies.users import get_users_service
from backend.exceptions.auth import EmailAlreadyExistError
from backend.jobs.auth import send_email_verification
from backend.redis_queue import job
from backend.schemas.auth import RegisterRequest
from backend.services.users_service import UsersService

router = APIRouter(prefix="/auth")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    register_request: RegisterRequest,
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
):

    try:
        job.enqueue(send_email_verification, register_request.email)

    except EmailAlreadyExistError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    @router.get("/verify-email")
    def verify_email(token: str):
        print(token)
