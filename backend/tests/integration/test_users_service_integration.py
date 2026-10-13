from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.dependencies.users import get_users_service
from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.models.users import UserRole, Users
from backend.schemas.users import CreateUserRequest
from backend.security.passwords import verify_password


def test_create_user_duplicate_email_with_whitespace(db: Session) -> None:
    service = get_users_service(db=db)
    password = "langes Passwort 123"

    request = CreateUserRequest(email="example@outlook.de", password=password)
    duplicate_request = CreateUserRequest(
        email="  example@outlook.de  ", password=password
    )

    assert duplicate_request.email == request.email

    service.create_user(create_user_request=request)

    with pytest.raises(EmailAlreadyExistError):
        service.create_user(create_user_request=duplicate_request)

    db.expunge_all()

    stmt = select(func.count()).select_from(Users).where(Users.email == request.email)
    count = db.execute(stmt).scalar_one()

    assert count == 1


def test_create_user_with_hash_like_password(db: Session) -> None:
    service = get_users_service(db=db)
    password = "$argon2id$v=19$m=65536,t=3,p=4$g2vGCeDo/CkiOu+XciV/Cw$akkU/Q1okx/ywuyb4U+0aMmahBYYBnDEWgQI7B10EIc"
    request = CreateUserRequest(email="example@outlook.de", password=password)

    user_created = service.create_user(create_user_request=request)

    assert user_created.hashed_password != password
    assert verify_password(password, user_created.hashed_password)


def test_create_user_duplicate(db: Session) -> None:
    service = get_users_service(db=db)
    password = "langes Passwort 123"
    request = CreateUserRequest(email="example@outlook.de", password=password)
    duplicate_request = CreateUserRequest(email="example@outlook.de", password=password)

    service.create_user(create_user_request=request)
    with pytest.raises(EmailAlreadyExistError, match="Email already exists"):
        service.create_user(create_user_request=duplicate_request)

    db.expunge_all()

    stmt = select(func.count()).select_from(Users).where(Users.email == request.email)
    count = db.execute(stmt).scalar_one()

    assert count == 1


def test_create_user(db: Session) -> None:
    service = get_users_service(db=db)
    password = "langes Passwort 123"
    request = CreateUserRequest(email="example@outlook.de", password=password)

    user_created = service.create_user(create_user_request=request)

    assert isinstance(user_created.id, UUID)
    assert user_created.email == "example@outlook.de"
    assert user_created.hashed_password != password
    assert verify_password(
        password=password, hashed_password=user_created.hashed_password
    )
    assert user_created.user_role == UserRole.CUSTOMER
    assert isinstance(user_created.created_at, datetime)
    assert isinstance(user_created.updated_at, datetime)

    user_id = user_created.id
    db.expunge_all()

    user_from_db = db.get(Users, user_id)

    assert user_from_db is not None
    assert user_from_db.email == request.email
