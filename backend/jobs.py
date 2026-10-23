import json
import logging
from functools import lru_cache
from typing import Any
from uuid import UUID

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint
from sentence_transformers import SentenceTransformer

from backend.config import (
    GPT_MODEL,
    OPENAI_API_KEY,
    QDRANT_CLIENT_URL,
    QDRANT_COLLECTION_NAME,
    TICKET_CLASSIFICATION_CONFIDENCE_THRESHOLD,
)
from backend.database import SessionLocal
from backend.exceptions.orders import OrderNotFoundError
from backend.exceptions.tickets import TicketRetrievalError
from backend.models.orders import Orders
from backend.models.tickets import TicketCategories, Tickets, TicketStatus
from backend.models.users import Users
from backend.repositories.orders_repository import OrdersRepository
from backend.schemas.tickets import ReplyDraft
from backend.services.llm_instructions import INSTRUCTIONS
from backend.services.llm_service import LLMService
from backend.services.ticket_classification_service import (
    TicketAnalysisResult,
    TicketClassificationService,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )


def embed_ticket_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text).tolist()


def classify_ticket(text: str) -> TicketAnalysisResult:
    service = TicketClassificationService()
    result = service.classify(text)
    return result


def requires_manual_review(confidence: float) -> bool:
    return confidence < TICKET_CLASSIFICATION_CONFIDENCE_THRESHOLD


def get_order(order_number: str, user_id: UUID) -> Orders:
    with SessionLocal.begin() as db:
        order = OrdersRepository(db).get_by_order_number(order_number, user_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_number} wurde nicht gefunden.")
        return order


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


def wait_for_review(ticket: Tickets, reason: str) -> None:
    ticket.status = TicketStatus.WAITING_FOR_APPROVAL
    ticket.review_reason = reason
    update_ticket(ticket)
    logger.info("Ticket %s wartet auf Pruefung: %s", ticket.id, reason)


def search_knowledge(query_vector: list[float]) -> list[ScoredPoint]:
    qdrant_client = QdrantClient(url=QDRANT_CLIENT_URL)
    try:
        result = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            query=query_vector,
            limit=3,
            with_payload=True,
            with_vectors=False,
        )
        return result.points
    finally:
        qdrant_client.close()


def generate_reply_draft(
    ticket_text: str, sources: list[dict[str, Any]], order: Orders | None = None
) -> ReplyDraft:
    order_data = (
        {"order_number": order.order_number, "status": order.status.value}
        if order is not None
        else None
    )
    prompt = json.dumps(
        {"ticket_text": ticket_text, "sources": sources, "order": order_data},
        ensure_ascii=False,
    )
    with OpenAI(api_key=OPENAI_API_KEY) as client:
        service = LLMService(client=client, model=GPT_MODEL)
        draft = service.generate_reply_draft(instructions=INSTRUCTIONS, prompt=prompt)
    available_ids = {source["id"] for source in sources}
    if not set(draft.source_ids).issubset(available_ids):
        raise ValueError("Antwortentwurf verweist auf unbekannte Quellen.")
    if not draft.source_ids:
        draft.needs_manual_review = True
    return draft


def process_ticket(ticket_id: UUID) -> None:
    ticket = get_ticket(ticket_id)
    if ticket.status != TicketStatus.PENDING:
        return

    ticket_analysis_result = classify_ticket(text=ticket.text)
    ticket.category = ticket_analysis_result.category
    if requires_manual_review(ticket_analysis_result.confidence):
        wait_for_review(ticket, "low_classification_confidence")
        return

    ticket.status = TicketStatus.PROCESSING
    order: Orders | None = None

    if ticket_analysis_result.order_number is not None:
        try:
            order = get_order(ticket_analysis_result.order_number, ticket.user_id)
            ticket.order_number = order.order_number
        except OrderNotFoundError:
            ticket.order_number = None
            wait_for_review(ticket, "order_not_found")
            return
    elif ticket.category != TicketCategories.TECHNICAL_FAQ:
        wait_for_review(ticket, "missing_order_number")
        return

    query_vector = embed_ticket_text(ticket.text)

    hits = search_knowledge(query_vector=query_vector)
    sources = [
        {
            "id": str(hit.id),
            "text": hit.payload["text"],
            "source": hit.payload["source"],
        }
        for hit in hits
        if hit.payload
        and isinstance(hit.payload.get("text"), str)
        and hit.payload["text"].strip()
        and isinstance(hit.payload.get("source"), str)
        and hit.payload["source"].strip()
    ]

    ticket.knowledge_sources = sources
    if not sources:
        wait_for_review(ticket, "no_knowledge_sources")
        return

    draft = generate_reply_draft(
        ticket_text=ticket.text,
        order=order,
        sources=sources,
    )

    ticket.reply_draft = draft.model_dump(mode="json")
    reason = "draft_requires_review" if draft.needs_manual_review else "draft_ready"
    wait_for_review(ticket, reason)
