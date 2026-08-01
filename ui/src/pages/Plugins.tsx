import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../services/dashboard";

export function Plugins() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading) return <div className="card">Loading plugins...</div>;
  if (error) return <div className="card">Error loading plugins</div>;

  return (
    <div className="card">
      <h3>Plugins</h3>
      <p>Loaded: {Array.isArray(data?.plugins) ? data.plugins.length : 0}</p>
    </div>
  );
}