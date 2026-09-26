import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";

interface Run {
  id: string;
  phase: string;
  status: string;
  total: number;
  completed: number;
  running_count: number;
  failed_count: number;
  queued_count: number;
}

interface Result {
  server_id: string;
  status: string;
  error_code: string | null;
  message: string | null;
  snapshot_id: string | null;
}

export function RunsPage() {
  const runs = useQuery({
    queryKey: ["runs"],
    queryFn: () => api<Run[]>("/api/v1/healthchecks"),
  });
  return (
    <section>
      <h1>Runs</h1>
      <ul className="plain">
        {(runs.data ?? []).map((run) => (
          <li key={run.id}>
            <Link to={`/runs/${run.id}`}>
              {run.phase} · {run.status} · {run.completed}/{run.total}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function RunDetailPage() {
  const { runId = "" } = useParams();
  const run = useQuery({
    queryKey: ["run", runId],
    queryFn: () => api<Run>(`/api/v1/healthchecks/${runId}`),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "QUEUED" || status === "RUNNING" ? 2000 : false;
    },
  });
  const results = useQuery({
    queryKey: ["run-results", runId],
    queryFn: () => api<Result[]>(`/api/v1/healthchecks/${runId}/results`),
    refetchInterval: run.data?.status === "QUEUED" || run.data?.status === "RUNNING" ? 2000 : false,
  });
  const data = run.data;
  const width = data && data.total ? Math.round((data.completed / data.total) * 100) : 0;
  return (
    <section>
      <h1>
        {data?.phase ?? "Run"} {data?.status}
      </h1>
      <div className="meter" aria-hidden="true">
        <span style={{ width: `${width}%` }} />
      </div>
      <p>
        {data?.completed ?? 0} / {data?.total ?? 0} · running {data?.running_count ?? 0} · failed{" "}
        {data?.failed_count ?? 0} · queued {data?.queued_count ?? 0}
      </p>
      <ul>
        {(results.data ?? []).map((result) => (
          <li key={result.server_id}>
            <Link to={`/servers/${result.server_id}`}>{result.server_id}</Link> · {result.status}
            {result.message ? ` · ${result.message}` : ""}
          </li>
        ))}
      </ul>
    </section>
  );
}
