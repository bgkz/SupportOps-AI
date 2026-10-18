from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.config import (
    TICKET_TEXT_MAX_LENGTH,
    TICKET_TEXT_MIN_LENGTH,
)
from backend.models.tickets import TicketCategories, TicketStatus


class CreateTicketRequest(BaseModel):
    user_id: UUID
    text: str = Field(
        min_length=TICKET_TEXT_MIN_LENGTH, max_length=TICKET_TEXT_MAX_LENGTH
    )


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    order_number: str | None = None
    text: str
    category: TicketCategories | None
    status: TicketStatus

    created_at: datetime
    updated_at: datetime
