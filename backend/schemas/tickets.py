from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.config import (
    TICKET_TEXT_MAX_LENGTH,
    TICKET_TEXT_MIN_LENGTH,
)
from backend.models.tickets import TicketCategories, TicketStatus


class ApproveTicketRequest(BaseModel):
    user_id: UUID
    approved: bool


class CreateTicketRequest(BaseModel):
    order_number: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}-\d{4}$",
    )
    text: str = Field(
        min_length=TICKET_TEXT_MIN_LENGTH, max_length=TICKET_TEXT_MAX_LENGTH
    )


# class CreateTicketRequest(BaseModel):
#     user_id: UUID
#     text: str = Field(
#         min_length=TICKET_TEXT_MIN_LENGTH, max_length=TICKET_TEXT_MAX_LENGTH
#     )


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    order_number: str | None = None
    text: str
    category: TicketCategories | None
    status: TicketStatus

    reply_draft: dict | None = None
    knowledge_sources: list[dict] | None = None
    review_reason: str | None = None
    approved: bool | None = None

    created_at: datetime
    updated_at: datetime


class ReplyDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply_text: str = Field(min_length=1)
    source_ids: list[str]
    needs_manual_review: bool
