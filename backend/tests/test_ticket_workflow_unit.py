from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from backend import jobs
from backend.models.tickets import TicketCategories, TicketStatus
from backend.schemas.tickets import ReplyDraft


@pytest.mark.parametrize("confidence,category,hits,reason", [
    (0.2, TicketCategories.DAMAGED_GOODS, [], "low_classification_confidence"),
    (0.9, TicketCategories.DAMAGED_GOODS, [], "missing_order_number"),
    (0.9, TicketCategories.TECHNICAL_FAQ, [], "no_knowledge_sources"),
    (0.9, TicketCategories.TECHNICAL_FAQ,
     [SimpleNamespace(id=1, payload={"text": "rule"})], "no_knowledge_sources"),
])
def test_review_paths(confidence, category, hits, reason):
    ticket = SimpleNamespace(id=uuid4(), user_id=uuid4(), text="Help please",
                             status=TicketStatus.PENDING)
    analysis = SimpleNamespace(category=category, confidence=confidence, order_number=None)
    with patch.object(jobs, "get_ticket", return_value=ticket), \
         patch.object(jobs, "classify_ticket", return_value=analysis), \
         patch.object(jobs, "embed_ticket_text", return_value=[0.1]), \
         patch.object(jobs, "search_knowledge", return_value=hits), \
         patch.object(jobs, "generate_reply_draft") as generate, \
         patch.object(jobs, "update_ticket") as save:
        jobs.process_ticket(ticket.id)
    assert ticket.status == TicketStatus.WAITING_FOR_APPROVAL
    assert ticket.review_reason == reason
    save.assert_called_once_with(ticket)
    generate.assert_not_called()


def test_faq_without_order_saves_draft():
    ticket = SimpleNamespace(id=uuid4(), user_id=uuid4(), text="Help please",
                             status=TicketStatus.PENDING)
    analysis = SimpleNamespace(category=TicketCategories.TECHNICAL_FAQ,
                               confidence=0.9, order_number=None)
    draft = ReplyDraft(reply_text="Read the guide", source_ids=["1"], needs_manual_review=False)
    with patch.object(jobs, "get_ticket", return_value=ticket), \
         patch.object(jobs, "classify_ticket", return_value=analysis), \
         patch.object(jobs, "embed_ticket_text", return_value=[0.1]), \
         patch.object(jobs, "search_knowledge", return_value=[
             SimpleNamespace(id=1, payload={"text": "rule", "source": "faq.md"})]), \
         patch.object(jobs, "generate_reply_draft", return_value=draft) as generate, \
         patch.object(jobs, "update_ticket"):
        jobs.process_ticket(ticket.id)
    assert generate.call_args.kwargs["order"] is None
    assert ticket.reply_draft["source_ids"] == ["1"]
    assert ticket.review_reason == "draft_ready"


def test_search_closes_client_on_failure():
    client = MagicMock()
    client.query_points.side_effect = RuntimeError("offline")
    with patch.object(jobs, "QdrantClient", return_value=client):
        with pytest.raises(RuntimeError):
            jobs.search_knowledge([0.1])
    client.close.assert_called_once()


def test_unknown_citation_is_rejected():
    client = MagicMock()
    draft = ReplyDraft(reply_text="Answer", source_ids=["invented"], needs_manual_review=False)
    with patch.object(jobs, "OpenAI", return_value=client), \
         patch.object(jobs, "LLMService") as service:
        service.return_value.generate_reply_draft.return_value = draft
        with pytest.raises(ValueError, match="unbekannte Quellen"):
            jobs.generate_reply_draft("Help", [{"id": "1", "text": "rule"}])
