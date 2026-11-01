import json
from typing import Any
from uuid import UUID

from openai import OpenAI

from backend.config import GPT_MODEL, OPENAI_API_KEY
from backend.database import SessionLocal
from backend.exceptions.orders import OrderNotFoundError
from backend.models.orders import Orders
from backend.repositories.orders_repository import OrdersRepository
from backend.schemas.tickets import ReplyDraft
from backend.services.llm_instructions import INSTRUCTIONS
from backend.services.llm_service import LLMService


def get_order(order_number: str, user_id: UUID) -> Orders:
    with SessionLocal.begin() as db:
        order = OrdersRepository(db).get_by_order_number(order_number, user_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_number} wurde nicht gefunden.")
        return order


def generate_reply_draft(
    ticket_text: str, sources: list[dict[str, Any]], order: dict[str, str] | None = None
) -> ReplyDraft:

    prompt = json.dumps(
        {"ticket_text": ticket_text, "sources": sources, "order": order},
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
