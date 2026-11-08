import type { User } from "../../types/user";

type SupportAgentDashboardProps = {
  user: User;
  onLogout: () => void;
};
export default function SupportAgentDashboard({
  user,
  onLogout,
}: SupportAgentDashboardProps) {
  return (
    <div className="support-agent-dashboard">
      <h1>Welcome AGENT, {user.email}!</h1>

      <button onClick={() => onLogout}>Logout</button>
    </div>
  );
}
