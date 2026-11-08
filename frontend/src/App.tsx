import { useState } from "react";
import "./App.css";
import LoginView from "./components/LoginView";
import type { User } from "./types/user";

import Dashboard from "./components/dashboard/Dashboard";

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
      {isLoggedIn && (
        <Dashboard user={user} onLogout={() => setUser(null)}></Dashboard>
      )}
    </div>
  );
}

export default App;
