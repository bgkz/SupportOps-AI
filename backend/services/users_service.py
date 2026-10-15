from uuid import UUID

from pydantic import EmailStr

from backend.exceptions.users import UserNotFoundError
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository
from backend.schemas.users import CreateUserRequest
from backend.security.passwords import hash_password


class UsersService:
    def __init__(self, users_repo: UsersRepository):
        self.users_repo = users_repo

    def change_email(self, user_id: UUID, new_email: EmailStr) -> Users:
        user = self.get_user(user_id=user_id)
        user.email = new_email.strip()

        return self.users_repo.update(user=user)

    def get_user(self, user_id: UUID) -> Users:
        user_found = self.users_repo.get(user_id)
        if user_found is None:
            raise UserNotFoundError("User not found")
        return user_found

    def create_user(self, create_user_request: CreateUserRequest) -> Users:
        hashed = hash_password(create_user_request.password.get_secret_value())
        return self.users_repo.add(
            Users(
                email=str(create_user_request.email),
                hashed_password=hashed,
                user_role=UserRole.CUSTOMER,
            )
        )
