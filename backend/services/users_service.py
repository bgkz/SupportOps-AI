from backend.models.users import Users
from backend.schemas.users import CreateUserRequest


class UsersService:
    def create_user(self, create_user_request: CreateUserRequest) -> Users:
        pass
