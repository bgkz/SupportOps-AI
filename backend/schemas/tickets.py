from uuid import UUID

from pydantic import BaseModel, Field

from backend.config import TICKET_TEXT_MAX_LENGTH, TICKET_TEXT_MIN_LENGTH


class CreateTicketRequest(BaseModel):
    user_id: UUID
    text: str = Field(
        min_length=TICKET_TEXT_MIN_LENGTH, max_length=TICKET_TEXT_MAX_LENGTH
    )
