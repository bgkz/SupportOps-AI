import { useEffect, useState } from "react";
import type { User } from "../../types/user";
import "./SupportAgentDashboard.css";

import { ticketSchema, type Ticket } from "../../types/tickets";
import TicketList from "./TicketList";
import TicketDetails from "./TicketDetails";
type SupportAgentDashboardProps = {
  user: User;
  onLogout: () => void;
};
export default function SupportAgentDashboard({
  user,
  onLogout,
}: SupportAgentDashboardProps) {
  const BASE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
  const [errorMessage, setErrorMessage] = useState("");
  const [allTickets, setAllTickets] = useState<Ticket[]>([]);
  const [showAllTickets, setShowAllTickets] = useState(false);

  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  const unresolvedTickets = allTickets.filter(
    (ticket) => ticket.status !== "resolved",
  );

  async function loadTickets() {
    try {
      const response = await fetch(`${BASE_BACKEND_URL}/tickets/`, {
        method: "GET",
        credentials: "include",
      });

      const data = await response.json();
      if (response.ok) {
        const result = ticketSchema.array().safeParse(data);
        if (!result.success) {
          setErrorMessage("The server returned an unexpected ticket format.");
          return;
        }
        setAllTickets(result.data);
      } else {
        if (typeof data.detail === "string") {
          setErrorMessage(data.detail);
        } else if (Array.isArray(data.detail)) {
          setErrorMessage(
            data.detail
              .map(
                (error: { loc: (string | number)[]; msg: string }) =>
                  `${error.loc.slice(1).join(".")}: ${error.msg}`,
              )
              .join(" | "),
          );
        } else {
          setErrorMessage(
            "An unexpected error occurred while loading the tickets.",
          );
          return;
        }
      }
    } catch {
      setErrorMessage("Unable to connect. Please try again");
      return;
    }
  }

  useEffect(() => {
    void loadTickets();
  }, []);

  function refresh() {
    void loadTickets();
  }

  return (
    <div className="support-agent-dashboard">
      <p>Welcome AGENT, {user.email}!</p>

      <div className="ticket-queue">
        <p>Ticket Queue</p>
        <div className="selector">
          <button onClick={() => setShowAllTickets(false)}>
            Pending Tickets ({unresolvedTickets.length})
          </button>
          <button onClick={() => setShowAllTickets(true)}>
            All Tickets ({allTickets.length})
          </button>
        </div>

        {showAllTickets && (
          <TicketList
            tickets={allTickets}
            onSelect={setSelectedTicket}
          ></TicketList>
        )}

        {!showAllTickets && (
          <TicketList
            tickets={unresolvedTickets}
            onSelect={setSelectedTicket}
          ></TicketList>
        )}
      </div>

      {selectedTicket && (
        <div className="modal-overlay" onClick={() => setSelectedTicket(null)}>
          <div
            className="modal-content"
            role="dialog"
            aria-modal="true"
            aria-label="Ticket details"
            onClick={(event) => event.stopPropagation()}
          >
            <TicketDetails ticket={selectedTicket} />
            <button onClick={() => setSelectedTicket(null)}>Schließen</button>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => {
          refresh();
        }}
      >
        Refresh ↻
      </button>

      <button onClick={onLogout}>Logout</button>
      {errorMessage && <p role="alert">{errorMessage}</p>}
    </div>
  );
}
