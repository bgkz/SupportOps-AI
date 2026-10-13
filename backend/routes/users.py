from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.users import CreateUserRequest
from backend.security.api_key import verify_api_key

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


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(create_user_request: CreateUserRequest):
    pass


@router.patch("/{user_id}")
def change_user(user_id: UUID):
    pass


@router.delete("/{user_id}")
def delete_user(user_id: UUID):
    pass
