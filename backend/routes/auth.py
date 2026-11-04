from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from backend.dependencies.users import get_users_service
from backend.exceptions.auth import EmailAlreadyExistError
from backend.schemas.auth import RegisterRequest
from backend.services.users_service import UsersService

router = APIRouter(prefix="/auth")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    register_request: RegisterRequest,
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
):

    try:
        ...
    except EmailAlreadyExistError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
