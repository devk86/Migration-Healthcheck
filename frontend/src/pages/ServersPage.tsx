import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";

interface Server {
  id: string;
  name: string;
  address: string;
  os_type: string;
  last_pre_check: string | null;
  last_post_check: string | null;
  current_status: string | null;
  last_connection_status: string | null;
}

export function ServersPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string[]>([]);
  const [osType, setOsType] = useState("");
  const servers = useQuery({
    queryKey: ["servers", osType],
    queryFn: () => api<Server[]>(`/api/v1/servers${osType ? `?os_type=${osType}` : ""}`),
  });
  const run = useMutation({
    mutationFn: (phase: "PRE" | "POST") =>
      api<{ id: string }>("/api/v1/healthchecks", {
        method: "POST",
        body: JSON.stringify({ server_ids: selected, phase }),
      }),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ["runs"] });
      navigate(`/runs/${result.id}`);
    },
  });

  function toggle(id: string) {
    setSelected((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  return (
    <section>
      <header className="page-head">
        <h1>Servers</h1>
        <div className="actions">
          <select value={osType} onChange={(event) => setOsType(event.target.value)} aria-label="OS filter">
            <option value="">All OS</option>
            <option value="linux">Linux</option>
            <option value="windows">Windows</option>
          </select>
          <button type="button" className="btn" disabled={!selected.length} onClick={() => run.mutate("PRE")}>
            Run PRE
          </button>
          <button type="button" className="btn" disabled={!selected.length} onClick={() => run.mutate("POST")}>
            Run POST
          </button>
        </div>
      </header>
      {run.isError ? <p className="fault">{run.error.message}</p> : null}
      <table className="grid">
        <thead>
          <tr>
            <th />
            <th>Server</th>
            <th>Address</th>
            <th>OS</th>
            <th>Last PRE</th>
            <th>Last POST</th>
            <th>Status</th>
            <th>Connection</th>
          </tr>
        </thead>
        <tbody>
          {(servers.data ?? []).map((server) => (
            <tr key={server.id}>
              <td>
                <input
                  type="checkbox"
                  checked={selected.includes(server.id)}
                  onChange={() => toggle(server.id)}
                  aria-label={`Select ${server.name}`}
                />
              </td>
              <td>
                <Link to={`/servers/${server.id}`}>{server.name}</Link>
              </td>
              <td>{server.address}</td>
              <td>{server.os_type}</td>
              <td>{formatTime(server.last_pre_check)}</td>
              <td>{formatTime(server.last_post_check)}</td>
              <td>{server.current_status ?? "—"}</td>
              <td>{server.last_connection_status ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {servers.data?.length === 0 ? <p>No servers yet. Import a CSV to add the first ones.</p> : null}
    </section>
  );
}

function formatTime(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleString();
}
