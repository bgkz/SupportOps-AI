import uuid
from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class TicketCategories(Enum):
    DAMAGED_GOODS = "damaged_goods"
    RETURN_REFUND = "return_refund"
    SHIPPING_STATUS = "shipping_status"
    INVOICE_PAYMENT = "invoice_payment"
    TECHNICAL_FAQ = "technical_faq"


class Tickets(Base):
    __tablename__ = "tickets"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_role: Mapped[TicketCategories] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=sa.func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()
    )
