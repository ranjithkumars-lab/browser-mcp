import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../services/dashboard";

export function Logs() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading) return <div className="card">Loading logs...</div>;
  if (error) return <div className="card">Error loading logs</div>;

  return (
    <div className="card">
      <h3>Logs</h3>
      <p>Event stream connected: {data ? "Yes" : "No"}</p>
    </div>
  );
}