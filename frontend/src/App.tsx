import { useState } from "react";
import "./App.css";
import LoginView from "./components/LoginView";
import type { User } from "./types/user";

import CustomerDashboard from "./components/customer-dashboard/CustomerDashboard";
import SupportAgentDashboard from "./components/support-agent-dashboard/SupportAgentDashboard";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const isLoggedIn = user !== null;

  return (
    <div className="main-app">
      {!isLoggedIn && (
        <>
          <LoginView onLogin={setUser} />
          <button>Make an Account</button>
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
