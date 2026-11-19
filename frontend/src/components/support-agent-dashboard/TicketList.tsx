import type { Ticket } from "../../types/tickets";
import "./TicketList.css";

type TicketListProps = {
  tickets: Ticket[];
};

export default function TicketList({ tickets }: TicketListProps) {
  return (
    <div className="ticket-list">
      {tickets.map((ticket) => (
        <div className="ticket-card" key={ticket.id}>
          <p>{ticket.text}</p>
          <p>{ticket.status}</p>
          <p>{ticket.created_at}</p>
        </div>
      ))}
    </div>
  );
}
