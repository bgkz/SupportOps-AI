import { useState } from "react";
import type { User } from "../../types/user";
import "./CustomerDashboard.css";

type CustomerDashboardProps = {
  user: User;
  onLogout: () => void;
};
export default function CustomerDashboard({
  user,
  onLogout,
}: CustomerDashboardProps) {
  const [openCreateTicketPopUp, setOpenCreateTicketPopUp] = useState(false);
  const [orderNumber, setOrderNumber] = useState("");

  return (
    <div className="customer-dashboard">
      <div className="customer-dashboard-header">
        <h2>My Customer Support Portal</h2>
        <p className="customer-dashboard-header-welcome-text">
          Welcome back, {user.email}! Here you can find your current requests
          and order updates.
        </p>
        <button
          className="customer-dashboard-header-create-new-ticket-btn"
          onClick={() => setOpenCreateTicketPopUp((prev) => !prev)}
        >
          + Create New Ticket
        </button>
      </div>

      {openCreateTicketPopUp && (
        <form className="customer-dashboard-create-new-ticket-popup-window">
          <div className="customer-dashboard-create-new-ticket-popup-window-input-order-number">
            <p>Affected order</p>
            <input
              className="customer-dashboard-create-new-ticket-popup-window-input-order-number"
              type="text"
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
              placeholder="AB-0042 (Ergonomic Wireless Mouse Pro)"
            />
          </div>

          <div className="customer-dashboard-create-new-ticket-popup-window-create-ticket-description-container">
            <p>Descirbe your Issue</p>
            <textarea
              id="ticket-description"
              placeholder="Please describe your issue in detail..."
              rows={8}
            />
          </div>

          <button type="submit">Submit</button>
          <button type="button" onClick={() => setOpenCreateTicketPopUp(false)}>
            Cancel
          </button>
        </form>
      )}

      <button onClick={() => onLogout}>Logout</button>
    </div>
  );
}
