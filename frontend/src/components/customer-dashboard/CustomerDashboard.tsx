import { useEffect, useState } from "react";
import { type User } from "../../types/user";
import "./CustomerDashboard.css";
import { ticketSchema, type Ticket } from "../../types/tickets";

import { orderSchema, type Order } from "../../types/order";
import TicketProgress from "./TicketProgress";
import "./TicketProgress.css";
type CustomerDashboardProps = {
  user: User;

  onLogout: () => void;
};
export default function CustomerDashboard({
  user,
  onLogout,
}: CustomerDashboardProps) {
  const BASE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

  const [openCreateTicketPopUp, setOpenCreateTicketPopUp] = useState(false);
  const [orderNumber, setOrderNumber] = useState("");
  const [issueDescription, setIssueDescription] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");

  const [orders, setOrders] = useState<Order[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);

  const ticket = tickets[0];
  const currentTicket = ticket
    ? {
        ticket,
        order: ticket.order_number
          ? (orders.find(
              (order) => order.order_number === ticket.order_number,
            ) ?? null)
          : null,
      }
    : null;

  function refresh() {
    void loadOrders(user);
    void loadTickets(user);
  }

  async function loadTickets(user: User) {
    try {
      const response = await fetch(`${BASE_BACKEND_URL}/tickets/${user.id}`, {
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
        setTickets(result.data);
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
      return [];
    }
  }

  async function loadOrders(user: User) {
    try {
      const response = await fetch(`${BASE_BACKEND_URL}/orders/${user.id}`, {
        method: "GET",
        credentials: "include",
      });

      const data = await response.json();
      if (response.ok) {
        const result = orderSchema.array().safeParse(data);
        if (!result.success) {
          setErrorMessage("The server returned an unexpected order format.");
          return;
        }
        setOrders(result.data);
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
            "An unexpected error occurred while loading the orders.",
          );
          return;
        }
      }
    } catch {
      setErrorMessage("Unable to connect. Please try again");
      return [];
    }
  }

  function openCreateTicket() {
    setErrorMessage("");
    setIdempotencyKey(crypto.randomUUID());
    setOpenCreateTicketPopUp((prev) => !prev);
  }

  function closeCreateTicket() {
    setErrorMessage("");
    setOpenCreateTicketPopUp(false);
  }

  async function handleCreateTicket(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    setErrorMessage("");
    if (!issueDescription.trim()) {
      setErrorMessage("Please describe your issue.");
      return;
    }

    try {
      const response = await fetch(BASE_BACKEND_URL + "/tickets/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({
          order_number: orderNumber.trim() || null,
          text: issueDescription,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setErrorMessage("Ticket created success");
        return;
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
          setErrorMessage("An unexpected error occurred.");
          return;
        }
        return;
      }
    } catch {
      setErrorMessage("Unable to connect. Please try again");
      return;
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadOrders(user);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadTickets(user);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  return (
    <div className="customer-dashboard">
      <div className="portal-header">
        <h2>My Customer Support Portal</h2>
        <p className="portal-welcome">
          Welcome back, {user.email}
          <br />
          Here you can find your current requests and order updates.
        </p>
        <button
          className="portal-create-ticket"
          onClick={() => openCreateTicket()}
        >
          + Create New Ticket
        </button>
      </div>

      <div className="portal-overview">
        <div className="portal-info-card">
          <p>Current Order</p>
          <p>{currentTicket?.order?.order_number ?? "No linked order"}</p>
        </div>
        <div className="portal-info-card">
          <p>Order Status</p>
          <p>{currentTicket?.order?.status ?? "No linked order"}</p>
        </div>

        <div className="portal-info-card">
          <p>Open Ticket</p>
          <p>
            {currentTicket?.ticket.text ?? "No ticket id"}{" "}
            {currentTicket?.ticket.status ?? "No ticket status"}
          </p>
        </div>
      </div>

      <div className="portal-ticket-summary">
        <p>{currentTicket?.ticket?.text}</p>
        <p>Created at: {currentTicket?.ticket?.created_at}</p>
        <p>{currentTicket?.ticket?.status}</p>
      </div>

      <p className="portal-workflow-title">Workflow Status</p>
      {currentTicket && currentTicket.ticket.status !== "resolved" && (
        <TicketProgress ticket={currentTicket.ticket} />
      )}

      {openCreateTicketPopUp && (
        <form className="portal-ticket-form" onSubmit={handleCreateTicket}>
          <div className="portal-form-field">
            <p>Affected order (optional)</p>
            <input
              className="portal-order-input"
              type="text"
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
              placeholder="AB-0042 (Ergonomic Wireless Mouse Pro)"
            />
          </div>

          <div className="portal-form-field">
            <label htmlFor="ticket-description">Describe your issue</label>
            <textarea
              id="ticket-description"
              placeholder="Please describe your issue in detail..."
              value={issueDescription}
              onChange={(e) => setIssueDescription(e.target.value)}
              rows={8}
            />
          </div>

          <button type="submit">Submit</button>
          <button type="button" onClick={closeCreateTicket}>
            Cancel
          </button>
        </form>
      )}

      <button
        className="portal-refresh"
        type="button"
        onClick={() => {
          refresh();
        }}
      >
        Refresh ↻
      </button>

      <button className="portal-logout" onClick={onLogout}>
        Logout
      </button>
      {errorMessage && <p role="alert">{errorMessage}</p>}
    </div>
  );
}
