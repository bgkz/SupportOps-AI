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
      <p>
        Welcome AGENT, {user.email} {user.id}!
      </p>

      <button onClick={onLogout}>Logout</button>
    </div>
  );
}
