import type { Ticket } from "../../types/tickets";
import "./TicketList.css";

type TicketListProps = {
  tickets: Ticket[];
  onSelect: (ticket: Ticket) => void;
};

export default function TicketList({ tickets, onSelect }: TicketListProps) {
  return (
    <div className="ticket-list">
      {tickets.map((ticket) => (
        <div
          className="ticket-card"
          key={ticket.id}
          onClick={() => onSelect(ticket)}
        >
          <p>{ticket.id}</p>
          <p>{ticket.text}</p>
          <p>{ticket.status}</p>
          <p>{ticket.created_at}</p>
        </div>
      ))}
    </div>
  );
}
