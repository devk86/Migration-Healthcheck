import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "../api/health";

const apiOrigin = import.meta.env.VITE_API_ORIGIN ?? "http://localhost:8000";

export function StatusPage() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 15000,
  });

  const ready = health.data?.status === "ok";
  const headline = health.isPending
    ? "Checking the lab"
    : health.isError
      ? "API unreachable"
      : ready
        ? "Lab is ready"
        : "Lab is degraded";

  return (
    <main className="console">
      <header className="mast">
        <p className="eyebrow">Migration bench</p>
        <h1>HealthCheck</h1>
        <p className="lede">
          Confirm this lab can record a server before the move and again after it.
        </p>
      </header>

      <section className="track" aria-label="Migration phases">
        <div className="station">
          <span className="phase">PRE</span>
          <span className="station-copy">Before migration</span>
        </div>
        <div className="path" aria-hidden="true">
          <span />
        </div>
        <div className="station post">
          <span className="phase">POST</span>
          <span className="station-copy">After migration</span>
        </div>
      </section>

      <section className="panel" aria-live="polite">
        <div className="panel-head">
          <h2>{headline}</h2>
          <p>
            {health.data
              ? `${health.data.service} ${health.data.version} · ${health.data.environment}`
              : "Waiting for the API"}
          </p>
        </div>

        {health.isError ? (
          <p className="fault">
            The browser could not reach <code>/api/v1/health</code>. Start the API and refresh.
          </p>
        ) : (
          <ul className="probes">
            {health.data
              ? Object.entries(health.data.checks).map(([name, status]) => (
                  <li key={name}>
                    <span className="probe-name">{name}</span>
                    <span className={status === "ok" ? "mark ok" : "mark bad"}>
                      {status === "ok" ? "Responding" : "Not responding"}
                    </span>
                  </li>
                ))
              : ["database", "redis"].map((name) => (
                  <li key={name}>
                    <span className="probe-name">{name}</span>
                    <span className="mark wait">Checking</span>
                  </li>
                ))}
          </ul>
        )}

        <a className="docs" href={`${apiOrigin}/docs`}>
          Open API docs
        </a>
      </section>
    </main>
  );
}
