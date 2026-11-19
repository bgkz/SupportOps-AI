import type { Ticket } from "../../types/tickets";
import "./TicketDetails.css";

type TicketDetailsProps = {
  ticket: Ticket;
};

export default function TicketDetails({ ticket }: TicketDetailsProps) {
  return (
    <div className="ticket-details">
      <p>{ticket.id}</p>
      <p>{ticket.text}</p>
    </div>
  );
}
