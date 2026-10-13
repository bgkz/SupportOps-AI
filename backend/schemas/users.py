from pydantic import BaseModel, EmailStr, Field, SecretStr


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=12)
