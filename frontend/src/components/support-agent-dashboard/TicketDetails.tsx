import type { Ticket } from "../../types/tickets";
import "./TicketDetails.css";

type TicketDetailsProps = {
  ticket: Ticket;
};

export default function TicketDetails({ ticket }: TicketDetailsProps) {
  return (
    <div className="ticket-details">
      <p>Review reason: {ticket.review_reason}</p>
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
      {ticket.knowledge_sources?.map((source, index) => (
        <div key={typeof source.id === "string" ? source.id : index}>
          <h4>{typeof source.source === "string" ? source.source : ""}</h4>
          <p style={{ whiteSpace: "pre-wrap" }}>
            {typeof source.text === "string" ? source.text : ""}
          </p>
        </div>
      ))}
      <div className="action-buttons">
        <button>✓ Approve Action & Reply</button>
        <button>⚠ Escalate (Tier 2)</button>
      </div>
    </div>
  );
}
