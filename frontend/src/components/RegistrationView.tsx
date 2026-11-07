import { useState } from "react";
import "./RegistrationView.css";

export default function RegistrationView() {
  const BASE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordRepeat, setPasswordRepeat] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleRegistration(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    setErrorMessage("");
    if (email.length == 0) {
      setErrorMessage("Error: Please enter your email address.");
      return;
    }
    if (password.length == 0) {
      setErrorMessage("Error: Please enter your password.");
      return;
    }
    if (passwordRepeat.length == 0) {
      setErrorMessage(
        "Error: Please enter the password in password repeat field",
      );
      return;
    }
    if (password != passwordRepeat) {
      setErrorMessage("Error: Passwords do not match.");
      return;
    }

    try {
      const response = await fetch(BASE_BACKEND_URL + "/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setErrorMessage(
          "We have sent an confirmation email, please check your email",
        );
        return;
      } else {
        setErrorMessage("Error: " + data.detail);
        return;
      }
    } catch {
      setErrorMessage("Unable to connect. Please try again");
    }
  }

  return (
    <form className="registration-form" onSubmit={handleRegistration}>
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
      <input
        type="password"
        placeholder="Repeat Password"
        value={passwordRepeat}
        onChange={(e) => setPasswordRepeat(e.target.value)}
      />

      {errorMessage && <p role="alert">{errorMessage}</p>}
      <button className="registration-form-submit-button" type="submit">
        Submit
      </button>
    </form>
  );
}
