from unittest.mock import MagicMock

import httpx
import pytest
from langgraph.checkpoint.memory import InMemorySaver
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException

from backend.config import QDRANT_COLLECTION_NAME
from backend.workflows.ticket_workflow import TicketWorkflow


def test_search_knowledge_propagates_qdrant_connection_error() -> None:
    client = MagicMock(spec=QdrantClient)
    error = ResponseHandlingException(
        httpx.ConnectError("Qdrant ist nicht erreichbar")
    )
    client.query_points.side_effect = error
    workflow = TicketWorkflow(
        ticket_classification_service=MagicMock(),
        sentence_transformer_model=MagicMock(),
        qdrant_client=client,
        checkpointer=InMemorySaver(),
    )
    query_vector = [0.1, 0.2, 0.3]

    with pytest.raises(ResponseHandlingException) as caught:
        workflow.search_knowledge_node({"embeddings": query_vector})

    assert caught.value is error
    client.query_points.assert_called_once_with(
        collection_name=QDRANT_COLLECTION_NAME,
        query=query_vector,
        limit=3,
        with_payload=True,
        with_vectors=False,
    )
