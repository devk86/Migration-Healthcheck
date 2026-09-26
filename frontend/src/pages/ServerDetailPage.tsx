import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";

interface Server {
  id: string;
  name: string;
  address: string;
  os_type: string;
  enabled: boolean;
  wave: string | null;
  current_status: string | null;
  last_connection_status: string | null;
}

interface SnapshotMeta {
  id: string;
  phase: string;
  checksum: string;
  created_at: string;
}

const tabs = ["Overview", "OS", "CPU", "Memory", "Disk", "Network", "Services", "Processes", "Software", "PRE", "POST", "Comparison", "Logs"] as const;

export function ServerDetailPage() {
  const { serverId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<(typeof tabs)[number]>("Overview");
  const [username, setUsername] = useState("");
  const [secret, setSecret] = useState("");
  const server = useQuery({
    queryKey: ["server", serverId],
    queryFn: () => api<Server>(`/api/v1/servers/${serverId}`),
  });
  const snapshots = useQuery({
    queryKey: ["snapshots", serverId],
    queryFn: () => api<SnapshotMeta[]>(`/api/v1/servers/${serverId}/snapshots`),
  });
  const pre = snapshots.data?.find((item) => item.phase === "PRE");
  const post = snapshots.data?.find((item) => item.phase === "POST");
  const activeSnapshot = tab === "POST" ? post : pre;
  const body = useQuery({
    queryKey: ["snapshot", activeSnapshot?.id],
    queryFn: () => api<Record<string, unknown>>(`/api/v1/snapshots/${activeSnapshot?.id}`),
    enabled: Boolean(activeSnapshot) && tab !== "Overview" && tab !== "Comparison" && tab !== "Logs",
  });
  const logs = useQuery({
    queryKey: ["logs", serverId],
    queryFn: () => api<{ logs: { phase: string; collector: string; commands: unknown[] }[] }>(`/api/v1/servers/${serverId}/logs`),
    enabled: tab === "Logs",
  });
  const kind = server.data?.os_type === "windows" ? "WINRM_PASSWORD" : "SSH_PASSWORD";
  const saveCredential = useMutation({
    mutationFn: () =>
      api(`/api/v1/servers/${serverId}/credentials`, {
        method: "POST",
        body: JSON.stringify({ kind, username, secret }),
      }),
    onSuccess: () => {
      setSecret("");
    },
  });
  const testConnection = useMutation({
    mutationFn: () => api<{ ok: boolean; message: string }>(`/api/v1/servers/${serverId}/test-connection`, { method: "POST" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["server", serverId] });
    },
  });
  const compare = useMutation({
    mutationFn: () =>
      api<{ id: string }>("/api/v1/comparisons", {
        method: "POST",
        body: JSON.stringify({ pre_snapshot_id: pre?.id, post_snapshot_id: post?.id }),
      }),
    onSuccess: (result) => navigate(`/comparisons/${result.id}`),
  });

  const sectionKey = tab.toLowerCase();
  const section = body.data?.[sectionKey];

  return (
    <section>
      <h1>{server.data?.name ?? "Server"}</h1>
      <p>
        {server.data?.address} · {server.data?.os_type} · {server.data?.current_status ?? "no comparison"} · connection{" "}
        {server.data?.last_connection_status ?? "unknown"}
      </p>
      <div className="tabs">
        {tabs.map((item) => (
          <button key={item} type="button" className={item === tab ? "btn" : "btn quiet"} onClick={() => setTab(item)}>
            {item}
          </button>
        ))}
      </div>
      {tab === "Overview" ? (
        <article className="panel">
          <p>Wave {server.data?.wave ?? "—"}</p>
          <p>Enabled {server.data?.enabled ? "yes" : "no"}</p>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              saveCredential.mutate();
            }}
          >
            <label>
              Username
              <input value={username} onChange={(event) => setUsername(event.target.value)} />
            </label>
            <label>
              Password or key
              <input type="password" value={secret} onChange={(event) => setSecret(event.target.value)} />
            </label>
            <button className="btn" type="submit">
              Save credential
            </button>
            <p>A credential saved here is used instead of the shared {server.data?.os_type ?? "OS"} credential.</p>
          </form>
          <button className="btn" type="button" onClick={() => testConnection.mutate()}>
            Test connection
          </button>
          {testConnection.data ? <p>{testConnection.data.message}</p> : null}
          {testConnection.isError ? <p className="fault">{testConnection.error.message}</p> : null}
        </article>
      ) : null}
      {tab === "Comparison" ? (
        <article className="panel">
          <button className="btn" type="button" disabled={!pre || !post} onClick={() => compare.mutate()}>
            Compare latest PRE and POST
          </button>
          {compare.isError ? <p className="fault">{compare.error.message}</p> : null}
        </article>
      ) : null}
      {tab === "Logs" ? (
        <article className="panel">
          {(logs.data?.logs ?? []).map((log) => (
            <pre key={log.phase}>{log.collector}</pre>
          ))}
        </article>
      ) : null}
      {tab !== "Overview" && tab !== "Comparison" && tab !== "Logs" ? (
        <article className="panel">
          <pre>{JSON.stringify(section ?? body.data ?? {}, null, 2)}</pre>
          {activeSnapshot ? <p>Checksum {activeSnapshot.checksum}</p> : <p>No {tab} snapshot yet.</p>}
        </article>
      ) : null}
      <p>
        <Link to="/servers">Back to servers</Link>
      </p>
    </section>
  );
}
