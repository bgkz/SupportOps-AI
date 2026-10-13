from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from backend.models.users import UserRole


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=12)


class CreateUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_role: UserRole
    email: EmailStr
    created_at: datetime
    updated_at: datetime
