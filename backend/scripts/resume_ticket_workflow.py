from uuid import UUID

from langgraph.checkpoint.postgres import PostgresSaver
from qdrant_client import QdrantClient

from backend.config import DATABASE_URL, QDRANT_CLIENT_URL
from backend.jobs import get_embedding_model
from backend.services.ticket_classification_service import (
    TicketClassificationService,
)
from backend.workflows.ticket_workflow import TicketWorkflow


def resume_ticket_workflow(ticket_id: UUID, approved: bool) -> dict:
    postgres_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)

    client = QdrantClient(url=QDRANT_CLIENT_URL)
    try:
        with PostgresSaver.from_conn_string(postgres_url) as checkpointer:
            workflow = TicketWorkflow(
                ticket_classification_service=TicketClassificationService(),
                sentence_transformer_model=get_embedding_model(),
                qdrant_client=client,
                checkpointer=checkpointer,
            )

            return workflow.resume(ticket_id, approved=approved)
    finally:
        client.close()
