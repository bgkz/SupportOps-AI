from uuid import UUID

from langgraph.checkpoint.postgres import PostgresSaver
from qdrant_client import QdrantClient

from backend.config import DATABASE_URL, QDRANT_CLIENT_URL
from backend.jobs import get_embedding_model, save_ticket_approval
from backend.services.ticket_classification_service import (
    TicketClassificationService,
)
from backend.workflows.ticket_workflow import TicketWorkflow


def main() -> None:
    ticket_id = UUID("d49f566f-193b-4c86-8fc3-61c3a2b1c650")
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

            result = workflow.resume(ticket_id, approved=True)
            save_ticket_approval(
                ticket_id=ticket_id,
                approved=result["approved"],
            )
            print("Freigegeben:", result["approved"])
    finally:
        client.close()


if __name__ == "__main__":
    main()
