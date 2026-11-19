import type { Ticket } from "../../types/tickets";
import "./TicketDetails.css";

type TicketDetailsProps = {
  ticket: Ticket;
};

export default function TicketDetails({ ticket }: TicketDetailsProps) {
  return (
    <div className="ticket-details">
      <p>Category: {ticket.category}</p>
      <div className="customer-ticket-text">
        <p>Original Ticket Query</p>
        <p>{ticket.text}</p>
      </div>
      <div className="ai-generated-reply-draft">
        <p>AI-Generated Reply Draft</p>
        <p>
          {typeof ticket.reply_draft?.reply_text === "string"
            ? ticket.reply_draft.reply_text
            : "Noch kein Entwurf"}
        </p>
      </div>
      <p>{JSON.stringify(ticket.knowledge_sources)}</p>
    </div>
  );
}
