import { useState } from "react";
import "./LoginView.css";
import { validateLogin } from "../utils/validation";
import { userSchema } from "../types/user";
import { errorSchema } from "../types/api";
import type { User } from "../types/user";

type LoginViewProps = {
  onLogin: (user: User) => void;
};

export default function LoginView({ onLogin }: LoginViewProps) {
  const BASE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleLogin(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    const error = validateLogin(email, password);
    setErrorMessage(error ?? "");
    if (error !== null) {
      return;
    }

    try {
      const response = await fetch(BASE_BACKEND_URL + "/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data: unknown = await response.json();
      if (response.ok) {
        const result = userSchema.safeParse(data);
        if (!result.success) {
          alert(result.error);
          setErrorMessage("The server response has an unexpected format.");
          return;
        }
        onLogin(result.data);
        setErrorMessage("Login successfull");
        return;
      } else {
        const result = errorSchema.safeParse(data);

        setErrorMessage(
          result.success
            ? "Error: " + result.data.detail
            : "An unexpected error occurred.",
        );
        return;
      }
    } catch {
      setErrorMessage("Unable to connect. Please try again");
    }
  }

  return (
    <form className="login-view" onSubmit={handleLogin}>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button type="submit">Log in</button>

      {errorMessage && <p role="alert">{errorMessage}</p>}
    </form>
  );
}
