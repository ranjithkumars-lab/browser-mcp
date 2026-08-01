import { useQuery } from "@tanstack/react-query";
import { getWorkers } from "../services/workers";

export function Workers() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["workers"],
    queryFn: getWorkers,
  });

  if (isLoading) return <div className="card">Loading workers...</div>;
  if (error) return <div className="card">Error loading workers</div>;

  return (
    <div className="card">
      <h3>Workers</h3>
      <p>Count: {Array.isArray(data) ? data.length : 0}</p>
    </div>
  );
}