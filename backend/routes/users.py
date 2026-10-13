from uuid import UUID

from fastapi import APIRouter, Depends

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


@router.post("/")
def create_user():
    pass


@router.patch("/{user_id}")
def change_user(user_id: UUID):
    pass


@router.delete("/{user_id}")
def delete_user(user_id: UUID):
    pass
