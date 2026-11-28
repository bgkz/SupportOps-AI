import { useState } from "react";
import "./App.css";
import LoginView from "./components/LoginView";
import type { User } from "./types/user";

import CustomerDashboard from "./components/customer-dashboard/CustomerDashboard";
import SupportAgentDashboard from "./components/support-agent-dashboard/SupportAgentDashboard";
import RegistrationView from "./components/RegistrationView";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [openRegistrationView, setOpenRegistrationView] = useState(false);

  const isLoggedIn = user !== null;

  return (
    <div className="main-app">
      {!isLoggedIn && (
        <>
          <LoginView onLogin={setUser} />

          <button onClick={() => setOpenRegistrationView((prev) => !prev)}>
            Make an Account
          </button>

          {openRegistrationView && (
            <div
              className="registration-overlay"
              onClick={() => setOpenRegistrationView(false)}
            >
              <div
                className="modal-content"
                role="dialog"
                aria-modal="true"
                aria-label="Registrierung"
                onClick={(event) => event.stopPropagation()}
              >
                <RegistrationView />
              </div>
            </div>
          )}
        </>
      )}
      {isLoggedIn && user.user_role === "customer" && (
        <CustomerDashboard
          user={user}
          onLogout={() => setUser(null)}
        ></CustomerDashboard>
      )}
      {isLoggedIn && user.user_role === "support_agent" && (
        <SupportAgentDashboard
          user={user}
          onLogout={() => setUser(null)}
        ></SupportAgentDashboard>
      )}
    </div>
  );
}

export default App;
