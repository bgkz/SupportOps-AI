import re
from dataclasses import dataclass
from typing import Callable, ContextManager

from typesafe_sdk import Choice, TypeSafeClient, TypeSafeError

from backend.exceptions.tickets import TicketClassificationError
from backend.models.tickets import TicketCategories


@dataclass(frozen=True)
class TicketAnalysisResult:
    category: TicketCategories
    confidence: float
    order_number: str | None


class TicketClassificationService:
    def __init__(
        self,
        model: str = "jev-latest",
        *,
        client_factory: Callable[..., ContextManager[TypeSafeClient]] = TypeSafeClient,
    ) -> None:
        self.model = model
        self.client_factory = client_factory

    def classify(self, text: str) -> TicketAnalysisResult:
        try:
            with self.client_factory(model=self.model) as client:
                response = client.system_one(
                    state=text,
                    questions={
                        "category": Choice(
                            instructions=(
                                "Ordne das Supportticket der passendsten Kategorie zu."
                            ),
                            criteria={
                                TicketCategories.DAMAGED_GOODS.value: "Beschädigte oder defekte Ware",
                                TicketCategories.RETURN_REFUND.value: "Rücksendung, Widerruf oder Erstattung",
                                TicketCategories.SHIPPING_STATUS.value: "Lieferstatus, verspätete oder fehlende Lieferung",
                                TicketCategories.INVOICE_PAYMENT.value: "Rechnungen, Zahlungen oder falsche Abbuchungen",
                                TicketCategories.TECHNICAL_FAQ.value: "Technische Fragen, Bedienung und Fehlerbehebung",
                            },
                        ),
                    },
                )
        except TypeSafeError as exc:
            raise TicketClassificationError(
                "Das Ticket konnte nicht klassifiziert werden."
            ) from exc

        answer = response.choices["category"]

        try:
            category = TicketCategories(answer.choice)
        except ValueError as exc:
            raise TicketClassificationError(
                f"Unbekannte Ticketkategorie: {answer.choice!r}"
            ) from exc

        order_numbers = {
            match.upper() for match in re.findall(r"\b[A-Za-z]{2}-[0-9]{4}\b", text)
        }

        return TicketAnalysisResult(
            category=category,
            confidence=answer.confidence,
            order_number=next(iter(order_numbers)) if len(order_numbers) == 1 else None,
        )
