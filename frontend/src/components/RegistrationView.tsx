import { useState } from "react";
import "./RegistrationView.css";

export default function RegistrationView() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordRepeat, setPasswordRepeat] = useState("");

  return (
    <form className="registration-form">
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
      <button className="registration-form-submit-button" type="submit">
        Submit
      </button>
    </form>
  );
}
