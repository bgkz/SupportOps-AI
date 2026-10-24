import logging
from functools import lru_cache
from uuid import UUID

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from backend.config import (
    QDRANT_CLIENT_URL,
)
from backend.database import SessionLocal
from backend.exceptions.tickets import TicketRetrievalError
from backend.models.tickets import TicketCategories, Tickets, TicketStatus
from backend.models.users import Users  # noqa: F401
from backend.services.ticket_classification_service import (
    TicketClassificationService,
)
from backend.workflows.ticket_workflow import TicketWorkflow

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )


def get_ticket(ticket_id: UUID) -> Tickets:
    with SessionLocal.begin() as db:
        ticket = db.get(Tickets, ticket_id)
        if ticket is None:
            raise TicketRetrievalError(f"Ticket {ticket_id} wurde nicht gefunden.")
        return ticket


def update_ticket(ticket: Tickets) -> Tickets:
    with SessionLocal.begin() as db:
        stored = db.get(Tickets, ticket.id, with_for_update=True)
        if stored is None:
            raise TicketRetrievalError(f"Ticket {ticket.id} wurde nicht gefunden.")
        # A duplicate job must not overwrite a completed review transition.
        if stored.status != TicketStatus.PENDING:
            return stored
        for field in (
            "category",
            "status",
            "order_number",
            "reply_draft",
            "knowledge_sources",
            "review_reason",
        ):
            setattr(stored, field, getattr(ticket, field))
        return stored


def process_ticket(ticket_id: UUID) -> None:
    ticket = get_ticket(ticket_id)
    if ticket.status != TicketStatus.PENDING:
        return

    client = QdrantClient(url=QDRANT_CLIENT_URL)
    try:
        workflow = TicketWorkflow(
            ticket_classification_service=TicketClassificationService(),
            sentence_transformer_model=get_embedding_model(),
            qdrant_client=client,
        )
        result = workflow.start(ticket)
    finally:
        client.close()

    ticket.category = TicketCategories(result["category"])
    ticket.status = TicketStatus(result["status"])
    ticket.order_number = result["order_number"]
    ticket.reply_draft = result["reply_draft"]
    ticket.knowledge_sources = result["sources"]
    ticket.review_reason = result["review_reason"]

    update_ticket(ticket)
