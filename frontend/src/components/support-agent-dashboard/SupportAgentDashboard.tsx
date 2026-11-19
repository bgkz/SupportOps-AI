import { useEffect, useState } from "react";
import type { User } from "../../types/user";
import "./SupportAgentDashboard.css";
import "./TicketList";

import { ticketSchema, type Ticket } from "../../types/tickets";
import TicketList from "./TicketList";
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

  const unresolvedTickets = allTickets.filter(
    (ticket) => ticket.status !== "resolved",
  );

  function refresh() {}

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

        {showAllTickets && <TicketList tickets={allTickets}></TicketList>}

        {!showAllTickets && (
          <TicketList tickets={unresolvedTickets}></TicketList>
        )}
      </div>

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
