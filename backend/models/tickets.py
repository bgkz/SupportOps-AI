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


class TicketStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Tickets(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        sa.CheckConstraint(
            "char_length(text) BETWEEN 10 AND 1000",
            name="ck_tickets_text_length",
        ),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_tickets_user_id_idempotency_key",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id"),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(sa.Text, nullable=False)

    category: Mapped[TicketCategories | None] = mapped_column(nullable=True)

    status: Mapped[TicketStatus] = mapped_column(
        nullable=False,
        default=TicketStatus.PENDING,
        server_default=TicketStatus.PENDING.name,
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=sa.func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()
    )

    idempotency_key: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
