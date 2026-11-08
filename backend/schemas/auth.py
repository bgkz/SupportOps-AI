from pydantic import BaseModel, EmailStr, Field, SecretStr

from backend.config import PASSWORD_MIN_LENGTH


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=PASSWORD_MIN_LENGTH)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=PASSWORD_MIN_LENGTH)
