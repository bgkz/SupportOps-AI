import { useEffect, useState } from "react";
import type { User } from "../../types/user";
import "./CustomerDashboard.css";

import { orderSchema, type Order } from "../../types/order";
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
        setErrorMessage("Orders retrieved successfully");
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
          return [];
        }
      }
    } catch {
      setErrorMessage("Unable to connect. Please try again");
      return [];
    }

    return [];
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

  return (
    <div className="customer-dashboard">
      <div className="customer-dashboard-header">
        <h2>My Customer Support Portal</h2>
        <p className="customer-dashboard-header-welcome-text">
          Welcome back, {user.email} {user.id}! Here you can find your current
          requests and order updates.
        </p>
        <button
          className="customer-dashboard-header-create-new-ticket-btn"
          onClick={() => openCreateTicket()}
        >
          + Create New Ticket
        </button>
      </div>

      <div className="customer-dashboard-order-information">
        <div className="customer-dashboard-order-information-order">
          <p>Current Order</p>
          <p>{orders[0]?.order_number ?? "No orders yet"}</p>
        </div>
      </div>

      {openCreateTicketPopUp && (
        <form
          className="customer-dashboard-create-new-ticket-popup-window"
          onSubmit={handleCreateTicket}
        >
          <div className="customer-dashboard-create-new-ticket-popup-window-input-order-number">
            <p>Affected order (optional)</p>
            <input
              className="customer-dashboard-create-new-ticket-popup-window-input-order-number"
              type="text"
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
              placeholder="AB-0042 (Ergonomic Wireless Mouse Pro)"
            />
          </div>

          <div className="customer-dashboard-create-new-ticket-popup-window-create-ticket-description-container">
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

      <button onClick={onLogout}>Logout</button>
      {errorMessage && <p role="alert">{errorMessage}</p>}
    </div>
  );
}
