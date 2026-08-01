import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../services/dashboard";

export function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading) return <div className="card">Loading dashboard...</div>;
  if (error) return <div className="card">Error loading dashboard</div>;

  return (
    <div className="card">
      <h3>Dashboard</h3>
      <div style={{ display: "grid", gap: "1rem", marginTop: "1rem" }}>
        <div>
          <strong>Jobs</strong>
          <p>Total: {data?.jobs.total ?? 0}</p>
          <p>Running: {data?.jobs.running ?? 0}</p>
          <p>Failed: {data?.jobs.failed ?? 0}</p>
        </div>
        <div>
          <strong>Workers</strong>
          <p>Available: {data?.workers.available ? "Yes" : "No"}</p>
        </div>
        <div>
          <strong>Plugins</strong>
          <p>Loaded: {Array.isArray(data?.plugins) ? data.plugins.length : 0}</p>
        </div>
      </div>
    </div>
  );
}