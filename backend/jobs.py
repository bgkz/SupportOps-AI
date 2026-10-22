from uuid import UUID

from backend.config import TICKET_CLASSIFICATION_CONFIDENCE_THRESHOLD
from backend.database import SessionLocal
from backend.exceptions.tickets import TicketRetrievalError
from backend.models.tickets import Tickets, TicketStatus
from backend.services.ticket_classification_service import (
    TicketAnalysisResult,
    TicketClassificationService,
)


def classify_ticket(text: str) -> TicketAnalysisResult:
    service = TicketClassificationService()
    result = service.classify(text)
    return result


def requires_manual_review(confidence: float) -> bool:
    return confidence < TICKET_CLASSIFICATION_CONFIDENCE_THRESHOLD


def process_ticket(ticket_id: UUID) -> None:
    with SessionLocal.begin() as db:
        ticket = db.get(Tickets, ticket_id)
        if ticket is None:
            raise TicketRetrievalError(f"Ticket {ticket_id} wurde nicht gefunden.")
        if ticket.status != TicketStatus.PENDING:
            return

        ticket_analysis_result = classify_ticket(text=ticket.text)
        ticket.category = ticket_analysis_result.category
        if ticket_analysis_result.order_number is not None:
            ticket.order_number = ticket_analysis_result.order_number

        if requires_manual_review(ticket_analysis_result.confidence):
            ticket.status = TicketStatus.WAITING_FOR_APPROVAL
        else:
            ticket.status = TicketStatus.PROCESSING
