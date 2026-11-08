import type { User } from "../../types/user";

type CustomerDashboardProps = {
  user: User;
  onLogout: () => void;
};
export default function CustomerDashboard({
  user,
  onLogout,
}: CustomerDashboardProps) {
  return (
    <div className="customer-dashboard">
      <h1>Welcome CUSTOMER, {user.email}!</h1>

      <button onClick={() => onLogout}>Logout</button>
    </div>
  );
}
