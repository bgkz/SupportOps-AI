import type { User } from "../../types/user";

type DashboardProps = {
  user: User;
  onLogout: () => void;
};
export default function Dashboard({ user, onLogout }: DashboardProps) {
  return (
    <div className="dashboard">
      <h1>Welcome, {user.email}!</h1>



      

      <button onClick={() => onLogout}>Logout</button>
    </div>
  );
}
