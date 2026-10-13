import uuid
from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.config import ORDER_NUMBER_MAX_LENGTH
from backend.database import Base


class OrderStatus(Enum):
    SHIPPED = "shipped"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Orders(Base):
    __tablename__ = "orders"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    order_number: Mapped[str] = mapped_column(
        String(ORDER_NUMBER_MAX_LENGTH), unique=True, nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=sa.func.now(),
    )

    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.PROCESSING)
