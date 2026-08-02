import { useQuery } from "@tanstack/react-query";
import { getDashboard, type Dashboard } from "../services/dashboard";

function StatusRow({ dashboard }: { dashboard: Dashboard }) {
  const plugins = Array.isArray(dashboard.plugins) ? dashboard.plugins.length : 0;
  const workersAvailable = Boolean(dashboard.workers?.available);
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
      <span className={`badge ${dashboard.jobs.failed > 0 ? "badge-warning" : "badge-success"}`}>
        {dashboard.jobs.failed} failed job{dashboard.jobs.failed === 1 ? "" : "s"}
      </span>
      <span className={`badge ${workersAvailable ? "badge-success" : "badge-danger"}`}>
        Workers {workersAvailable ? "online" : "offline"}
      </span>
      <span className="badge badge-info">{plugins} plugins</span>
      <span className="badge badge-accent">{dashboard.jobs.running} running</span>
    </div>
  );
}

export function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading) {
    return (
      <div aria-busy="true">
        <div className="stats-grid">
          {[0, 1, 2, 3].map((i) => (
            <div className="stat-card" key={i}>
              <div className="skeleton" style={{ height: "0.875rem", width: "5rem" }} />
              <div className="skeleton" style={{ height: "2rem", width: "4rem", marginTop: "0.75rem" }} />
            </div>
          ))}
        </div>
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="alert alert-error" role="alert">
        Error loading dashboard. Check that the API server is reachable.
      </div>
    );
  }

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total jobs</div>
          <div className="stat-value">{data.jobs.total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Running</div>
          <div className="stat-value">{data.jobs.running}</div>
          <div className="stat-trend">
            <span className="badge badge-info">in flight</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Failed</div>
          <div className="stat-value">{data.jobs.failed}</div>
          <div className="stat-trend">
            <span className={`badge ${data.jobs.failed > 0 ? "badge-danger" : "badge-success"}`}>
              {data.jobs.failed > 0 ? "needs attention" : "all clear"}
            </span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Workers</div>
          <div className="stat-value">{data.workers?.available ? "Online" : "Offline"}</div>
          <div className="stat-trend">
            <span className={`badge ${data.workers?.available ? "badge-success" : "badge-muted"}`}>
              {data.workers?.available ? "ready" : "unavailable"}
            </span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Plugins</div>
          <div className="stat-value">{Array.isArray(data.plugins) ? data.plugins.length : 0}</div>
          <div className="stat-trend">
            <span className="badge badge-accent">registered</span>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">System status</div>
        <div className="card-sub" style={{ marginBottom: "var(--space-4)" }}>
          Live state from the API gateway
        </div>
        <StatusRow dashboard={data} />
      </div>
    </div>
  );
}
