from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies.users import get_users_service
from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.schemas.users import CreateUserRequest, CreateUserResponse
from backend.security.api_key import verify_api_key
from backend.services.users_service import UsersService

router = APIRouter(
    prefix="/users",
    dependencies=[Depends(verify_api_key)],
)


@router.get("/")
def list_users():
    pass


@router.get("/{user_id}")
def get_user(user_id: UUID):
    pass


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=CreateUserResponse
)
def create_user(
    create_user_request: CreateUserRequest,
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
):
    try:
        return users_service.create_user(create_user_request=create_user_request)
    except EmailAlreadyExistError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except UserCreationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@router.patch("/{user_id}")
def change_user(user_id: UUID):
    pass


@router.delete("/{user_id}")
def delete_user(user_id: UUID):
    pass
