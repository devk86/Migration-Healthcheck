import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { api } from "../api/client";

interface ImportBody {
  mode: string;
  imported: number;
  rows: { line: number; name: string; os_type: string }[];
  errors: { line: number; message: string }[];
}

export function ImportPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportBody | null>(null);
  const [error, setError] = useState("");
  const blocked = Boolean(result && result.errors.length > 0);

  async function submit(mode: "preview" | "import", event?: FormEvent) {
    event?.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setError("");
    const body = new FormData();
    body.set("file", file);
    body.set("mode", mode);
    try {
      const response = await api<ImportBody>("/api/v1/imports/servers", { method: "POST", body });
      setResult(response);
      if (mode === "import" && response.imported > 0) {
        await queryClient.invalidateQueries({ queryKey: ["servers"] });
        await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Import failed.");
    }
  }

  return (
    <section>
      <h1>Import servers</h1>
      <p>CSV columns: Server name/IP, OS name. Do not put credentials in the file.</p>
      <form className="panel" onSubmit={(event) => submit("preview", event)}>
        <input
          type="file"
          accept=".csv,text/csv"
          onClick={(event) => {
            event.currentTarget.value = "";
          }}
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setResult(null);
            setError("");
          }}
        />
        <div className="actions">
          <button className="btn" type="submit">
            Preview
          </button>
          <button className="btn" type="button" disabled={!file || blocked} onClick={() => submit("import")}>
            Import
          </button>
        </div>
      </form>
      {error ? <p className="fault">{error}</p> : null}
      {result ? (
        <article className="panel">
          <p>{summary(result)}</p>
          <ul>
            {result.errors.map((item) => (
              <li key={`${item.line}-${item.message}`}>
                Line {item.line}: {item.message}
              </li>
            ))}
          </ul>
          <ul>
            {result.rows.map((row) => (
              <li key={`${row.line}-${row.name}`}>
                {row.name} · {row.os_type}
              </li>
            ))}
          </ul>
        </article>
      ) : null}
    </section>
  );
}

function summary(result: ImportBody): string {
  const count = result.mode === "import" ? result.imported : result.rows.length;
  const label = count === 1 ? "server" : "servers";
  if (result.errors.length > 0) {
    return `No servers were added. Fix ${result.errors.length} row error${result.errors.length === 1 ? "" : "s"} and try again.`;
  }
  if (result.mode === "import") {
    return `Imported ${count} ${label}.`;
  }
  return `${count} ${label} ready. Nothing is saved until you click Import.`;
}
