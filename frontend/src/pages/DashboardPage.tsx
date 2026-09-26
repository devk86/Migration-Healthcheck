import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";

interface Dashboard {
  total_servers: number;
  pre_completed: number;
  post_completed: number;
  pass_count: number;
  warning_count: number;
  failure_count: number;
  connection_errors: number;
  os_distribution: { os_type: string; count: number }[];
  failures_by_category: { category: string; count: number }[];
  recent_runs: { id: string; phase: string; status: string; completed: number; total: number }[];
}

export function DashboardPage() {
  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<Dashboard>("/api/v1/dashboard"),
  });
  const data = dashboard.data;
  return (
    <section>
      <h1>Dashboard</h1>
      {dashboard.isError ? <p className="fault">Dashboard data is unavailable.</p> : null}
      <div className="kpis">
        <Kpi label="Servers" value={data?.total_servers} />
        <Kpi label="PRE completed" value={data?.pre_completed} />
        <Kpi label="POST completed" value={data?.post_completed} />
        <Kpi label="Pass" value={data?.pass_count} />
        <Kpi label="Warning" value={data?.warning_count} />
        <Kpi label="Failure" value={data?.failure_count} />
        <Kpi label="Connection errors" value={data?.connection_errors} />
      </div>
      <div className="chart-grid">
        <article className="panel">
          <h2>OS distribution</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data?.os_distribution ?? []}>
              <XAxis dataKey="os_type" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#1f6f8b" />
            </BarChart>
          </ResponsiveContainer>
        </article>
        <article className="panel">
          <h2>Failures by category</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data?.failures_by_category ?? []}>
              <XAxis dataKey="category" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#c4622d" />
            </BarChart>
          </ResponsiveContainer>
        </article>
      </div>
      <article className="panel">
        <h2>Recent runs</h2>
        <ul className="plain">
          {(data?.recent_runs ?? []).map((run) => (
            <li key={run.id}>
              {run.phase} · {run.status} · {run.completed}/{run.total}
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}

function Kpi({ label, value }: { label: string; value: number | undefined }) {
  return (
    <article className="kpi">
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
    </article>
  );
}
