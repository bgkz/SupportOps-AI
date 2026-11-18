import type { Ticket } from "../../types/tickets";

type TicketProgressProps = {
  ticket: Ticket;
};

export default function TicketProgress({ ticket }: TicketProgressProps) {
  return (
    <div className="ticket-progress-container">
      {(ticket.status === "pending" || ticket.status === "processing") && (
        <>
          <p>Ticket submitted!</p>
          <span
            className="step-completed"
            role="img"
            aria-label="Abgeschlossen"
          >
            ✓
          </span>
          <p>We’re reviewing the information and preparing a response.</p>
          <span className="step-pending" role="img" aria-label="Noch offen" />
        </>
      )}

      {ticket.status == "waiting_for_approval" && (
        <>
          <p>Ticket submitted!</p>
          <span
            className="step-completed"
            role="img"
            aria-label="Abgeschlossen"
          >
            ✓
          </span>
          <p>Reviewed information and prepared response! </p>
          <span
            className="step-completed"
            role="img"
            aria-label="Abgeschlossen"
          >
            ✓
          </span>
          <p>Waiting for approval by our support agent</p>
          <span className="step-pending" role="img" aria-label="Noch offen" />
        </>
      )}

      {ticket.status == "escalated" && (
        <>
          <p>Ticket submitted!</p>
          <span
            className="step-completed"
            role="img"
            aria-label="Abgeschlossen"
          >
            ✓
          </span>
          <p>Reviewed information and prepared response! </p>
          <span
            className="step-completed"
            role="img"
            aria-label="Abgeschlossen"
          >
            ✓
          </span>
          <p>Waiting for approval by our support agent</p>
          <span className="step-pending" role="img" aria-label="Noch offen" />

          <p>Send to 2nd Level Support (Expert)</p>
          <span
            className="step-completed"
            role="img"
            aria-label="Abgeschlossen"
          >
            ✓
          </span>
        </>
      )}
    </div>
  );
}
