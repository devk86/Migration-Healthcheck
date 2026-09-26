import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";

interface GlobalCredential {
  os_type: string;
  kind: string;
  username: string;
}

const linuxKinds = [
  ["SSH_PASSWORD", "SSH password"],
  ["SSH_PRIVATE_KEY", "SSH private key"],
] as const;

export function CredentialsPage() {
  const saved = useQuery({
    queryKey: ["global-credentials"],
    queryFn: () => api<GlobalCredential[]>("/api/v1/credentials/global"),
  });
  return (
    <section>
      <h1>Credentials</h1>
      <p>One Linux credential and one Windows credential apply to every server that does not have its own.</p>
      <div className="chart-grid">
        <CredentialForm
          osType="linux"
          title="Linux"
          current={saved.data?.find((item) => item.os_type === "linux")}
        />
        <CredentialForm
          osType="windows"
          title="Windows"
          current={saved.data?.find((item) => item.os_type === "windows")}
        />
      </div>
    </section>
  );
}

function CredentialForm({
  osType,
  title,
  current,
}: {
  osType: "linux" | "windows";
  title: string;
  current: GlobalCredential | undefined;
}) {
  const queryClient = useQueryClient();
  const [kind, setKind] = useState(osType === "windows" ? "WINRM_PASSWORD" : "SSH_PASSWORD");
  const [username, setUsername] = useState("");
  const [secret, setSecret] = useState("");
  const [savedMessage, setSavedMessage] = useState("");
  const [loaded, setLoaded] = useState(false);
  if (current && !loaded) {
    setKind(current.kind);
    setUsername(current.username);
    setLoaded(true);
  }
  const save = useMutation({
    mutationFn: () =>
      api(`/api/v1/credentials/global/${osType}`, {
        method: "PUT",
        body: JSON.stringify({ kind, username, secret }),
      }),
    onSuccess: () => {
      setSecret("");
      setSavedMessage("Saved. The secret is not shown again.");
      void queryClient.invalidateQueries({ queryKey: ["global-credentials"] });
    },
  });
  return (
    <form
      className="panel"
      onSubmit={(event) => {
        event.preventDefault();
        setSavedMessage("");
        save.mutate();
      }}
    >
      <h2>{title}</h2>
      {current ? (
        <p>
          In use as {current.username} · {labelFor(current.kind)}
        </p>
      ) : (
        <p>Not configured.</p>
      )}
      {osType === "linux" ? (
        <label>
          Type
          <select value={kind} onChange={(event) => setKind(event.target.value)}>
            {linuxKinds.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <p>WinRM password</p>
      )}
      <label>
        Username
        <input value={username} onChange={(event) => setUsername(event.target.value)} />
      </label>
      <label>
        {kind === "SSH_PRIVATE_KEY" ? "Private key" : "Password"}
        {kind === "SSH_PRIVATE_KEY" ? (
          <textarea value={secret} onChange={(event) => setSecret(event.target.value)} rows={6} />
        ) : (
          <input type="password" value={secret} onChange={(event) => setSecret(event.target.value)} />
        )}
      </label>
      <button className="btn" type="submit" disabled={save.isPending}>
        Save {title} credential
      </button>
      {savedMessage ? <p>{savedMessage}</p> : null}
      {save.isError ? <p className="fault">{save.error.message}</p> : null}
    </form>
  );
}

function labelFor(kind: string): string {
  if (kind === "SSH_PRIVATE_KEY") {
    return "SSH private key";
  }
  if (kind === "WINRM_PASSWORD") {
    return "WinRM password";
  }
  return "SSH password";
}
