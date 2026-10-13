import uuid
from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class UserRole(Enum):
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"


class Users(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_role: Mapped[UserRole] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=sa.func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=sa.func.now(),
    )
