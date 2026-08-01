import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../services/dashboard";

export function Jobs() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading) return <div className="card">Loading jobs...</div>;
  if (error) return <div className="card">Error loading jobs</div>;

  return (
    <div className="card">
      <h3>Jobs</h3>
      <p>Total: {data?.jobs.total ?? 0}</p>
      <p>Running: {data?.jobs.running ?? 0}</p>
      <p>Failed: {data?.jobs.failed ?? 0}</p>
    </div>
  );
}