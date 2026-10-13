from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository
from backend.schemas.users import CreateUserRequest
from backend.security.passwords import hash_password


class UsersService:
    def __init__(self, users_repo: UsersRepository):
        self.users_repo = users_repo

    def create_user(self, create_user_request: CreateUserRequest) -> Users:
        hashed = hash_password(create_user_request.password.get_secret_value())
        return self.users_repo.add(
            Users(
                email=str(create_user_request.email),
                hashed_password=hashed,
                user_role=UserRole.CUSTOMER,
            )
        )
