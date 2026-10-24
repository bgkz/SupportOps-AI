from typing import TypedDict
from uuid import UUID

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from openai import OpenAIError
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from backend.config import (
    QDRANT_COLLECTION_NAME,
    TICKET_CLASSIFICATION_CONFIDENCE_THRESHOLD,
)
from backend.exceptions.orders import OrderNotFoundError
from backend.models.tickets import Tickets
from backend.services.ticket_classification_service import (
    TicketAnalysisResult,
    TicketClassificationService,
)
from backend.services.ticket_processing_service import generate_reply_draft, get_order


class TicketState(TypedDict):
    text: str
    category: str
    confidence: float
    order_number: str | None
    status: str
    user_id: str
    order: dict[str, str] | None
    review_reason: str | None
    sources: list[dict[str, str]]
    embeddings: list[float]
    reply_draft: dict | None
    approved: bool | None


class TicketWorkflow:
    def classify_ticket_node(self, state: TicketState) -> dict:
        result: TicketAnalysisResult = self.ticket_classification_service.classify(
            state["text"]
        )

        return {
            "category": result.category.value,
            "confidence": result.confidence,
            "order_number": result.order_number,
        }

    def route_after_classification(self, state: TicketState) -> str:
        if state["confidence"] < TICKET_CLASSIFICATION_CONFIDENCE_THRESHOLD:
            return "review"

        return "continue"

    def manual_review_node(self, state: TicketState) -> dict:
        return {
            "status": "waiting_for_approval",
            "review_reason": (
                state["review_reason"] or "low_classification_confidence"
            ),
        }

    def continue_processing_node(self, state: TicketState) -> dict:
        return {"status": "processing"}

    def check_order_node(self, state: TicketState) -> dict:
        order_number = state["order_number"]
        if order_number is None:
            if state["category"] == "technical_faq":
                return {"order": None, "review_reason": None}

            return {
                "order": None,
                "review_reason": "missing_order_number",
                "status": "waiting_for_approval",
            }

        try:
            order = get_order(
                order_number=order_number,
                user_id=UUID(state["user_id"]),
            )
        except OrderNotFoundError:
            return {
                "order": None,
                "status": "waiting_for_approval",
                "review_reason": "order_not_found",
            }
        return {
            "order": {
                "order_number": order.order_number,
                "status": order.status.value,
            },
            "review_reason": None,
        }

    def route_after_check_status(self, state: TicketState) -> str:
        if state["status"] == "waiting_for_approval":
            return "review"

        return "continue"

    def embed_ticket_text_node(self, state: TicketState) -> dict:
        try:
            return {
                "embeddings": self.sentence_transformer_model.encode(
                    state["text"]
                ).tolist()
            }
        except RuntimeError as error:
            return {
                "status": "waiting_for_approval",
                "review_reason": f"embedding_error {error}",
            }

    def search_knowledge_node(self, state: TicketState) -> dict:
        try:
            result = self.qdrant_client.query_points(
                collection_name=QDRANT_COLLECTION_NAME,
                query=state["embeddings"],
                limit=3,
                with_payload=True,
                with_vectors=False,
            )

            sources = [
                {
                    "id": str(hit.id),
                    "text": hit.payload["text"],
                    "source": hit.payload["source"],
                }
                for hit in result.points
                if hit.payload
                and isinstance(hit.payload.get("text"), str)
                and hit.payload["text"].strip()
                and isinstance(hit.payload.get("source"), str)
                and hit.payload["source"].strip()
            ]

            if not sources:
                return {
                    "sources": [],
                    "status": "waiting_for_approval",
                    "review_reason": "no_knowledge_sources",
                }

            return {"sources": sources}

        except RuntimeError as error:
            return {
                "status": "waiting_for_approval",
                "review_reason": f"search_knowledge_error {error}",
            }

    def generate_draft_node(self, state: TicketState) -> dict:
        try:
            draft = generate_reply_draft(
                ticket_text=state["text"],
                sources=state["sources"],
                order=state["order"],
            )
            return {
                "reply_draft": draft.model_dump(mode="json"),
                "status": "waiting_for_approval",
                "review_reason": (
                    "draft_requires_review"
                    if draft.needs_manual_review
                    else "draft_ready"
                ),
            }

        except (OpenAIError, ValueError) as error:
            return {
                "status": "waiting_for_approval",
                "review_reason": f"generate_reply_draft {error}",
            }

    def __init__(
        self,
        ticket_classification_service: TicketClassificationService,
        sentence_transformer_model: SentenceTransformer,
        qdrant_client: QdrantClient,
    ) -> None:
        self.ticket_classification_service = ticket_classification_service
        self.sentence_transformer_model = sentence_transformer_model
        self.qdrant_client = qdrant_client

        self.routing_builder = StateGraph(TicketState)
        self.routing_builder.add_node("classify_ticket", self.classify_ticket_node)
        self.routing_builder.add_node("manual_review", self.manual_review_node)
        self.routing_builder.add_node(
            "continue_processing", self.continue_processing_node
        )
        self.routing_builder.add_node("check_order", self.check_order_node)
        self.routing_builder.add_node("embed_ticket_text", self.embed_ticket_text_node)
        self.routing_builder.add_node("search_knowledge", self.search_knowledge_node)
        self.routing_builder.add_node("generate_draft", self.generate_draft_node)

        self.routing_builder.add_conditional_edges(
            "classify_ticket",
            self.route_after_classification,
            {
                "continue": "continue_processing",
                "review": "manual_review",
            },
        )

        transitions = {
            "check_order": "embed_ticket_text",
            "embed_ticket_text": "search_knowledge",
            "search_knowledge": "generate_draft",
        }

        for source, next_node in transitions.items():
            self.routing_builder.add_conditional_edges(
                source,
                self.route_after_check_status,
                {
                    "continue": next_node,
                    "review": "manual_review",
                },
            )

        self.routing_builder.add_edge(START, "classify_ticket")
        self.routing_builder.add_edge("manual_review", END)
        self.routing_builder.add_edge("continue_processing", "check_order")
        self.routing_builder.add_edge("generate_draft", END)

        self.routing_graph = self.routing_builder.compile(checkpointer=InMemorySaver())

    def start(self, ticket: Tickets):
        return self.routing_graph.invoke(
            {
                "text": ticket.text,
                "user_id": str(ticket.user_id),
                "category": "",
                "confidence": 0.0,
                "order_number": None,
                "status": "pending",
                "order": None,
                "review_reason": None,
                "sources": [],
                "embeddings": [],
                "reply_draft": None,
                "approved": None,
            },
            config={"configurable": {"thread_id": str(ticket.id)}},
        )
