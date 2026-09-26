import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, getToken } from "../api/client";

interface ReportChoice {
  server_id: string;
  server_name: string;
  kind: "pre" | "post" | "comparison";
  snapshot_id: string | null;
  comparison_id: string | null;
}

const kindLabel: Record<ReportChoice["kind"], string> = {
  pre: "PRE",
  post: "POST",
  comparison: "Comparison",
};

interface Report {
  id: string;
  format: string;
  comparison_id: string;
  created_at: string;
}

export function ReportsPage() {
  const queryClient = useQueryClient();
  const choices = useQuery({
    queryKey: ["report-choices"],
    queryFn: () => api<ReportChoice[]>("/api/v1/reports/choices"),
  });
  const reports = useQuery({
    queryKey: ["reports"],
    queryFn: () => api<Report[]>("/api/v1/reports"),
  });
  const [selection, setSelection] = useState("");
  const [format, setFormat] = useState("html");
  const [downloadError, setDownloadError] = useState("");
  const selected = (choices.data ?? []).find((item) => `${item.server_id}:${item.kind}` === selection);
  const create = useMutation({
    mutationFn: () =>
      api<Report>("/api/v1/reports", {
        method: "POST",
        body: JSON.stringify({ comparison_id: selected?.comparison_id, format }),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });

  async function downloadDocument() {
    if (!selected) {
      return;
    }
    let current = selected;
    if (current.kind === "comparison" && !current.comparison_id) {
      const fresh = await queryClient.fetchQuery({
        queryKey: ["report-choices"],
        queryFn: () => api<ReportChoice[]>("/api/v1/reports/choices"),
      });
      current = fresh.find((item) => `${item.server_id}:${item.kind}` === selection) ?? current;
    }
    const path =
      current.kind === "comparison" && current.comparison_id
        ? `/api/v1/reports/documents/${current.comparison_id}/comparison`
        : current.snapshot_id
          ? `/api/v1/reports/snapshots/${current.snapshot_id}/html`
          : "";
    if (!path) {
      setDownloadError(
        current.kind === "comparison"
          ? "Run a POST check before downloading the comparison report."
          : "This report is not ready to download.",
      );
      return;
    }
    setDownloadError("");
    const headers = new Headers();
    const token = getToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    const response = await fetch(path, { headers });
    if (!response.ok) {
      setDownloadError("The HTML file could not be downloaded.");
      return;
    }
    const blob = await response.blob();
    const match = /filename="([^"]+)"/.exec(response.headers.get("content-disposition") ?? "");
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = match?.[1] ?? `${selected.kind}.html`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function download(report: Report) {
    const headers = new Headers();
    const token = getToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    const response = await fetch(`/api/v1/reports/${report.id}/download`, { headers });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `report.${report.format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section>
      <h1>Reports</h1>
      <div className="actions">
        <select aria-label="Report" value={selection} onChange={(event) => setSelection(event.target.value)}>
          <option value="">Choose a report</option>
          {(choices.data ?? []).map((item) => (
            <option key={`${item.server_id}-${item.kind}`} value={`${item.server_id}:${item.kind}`}>
              {item.server_name} · {kindLabel[item.kind]}
            </option>
          ))}
        </select>
        <button className="btn" type="button" disabled={!selected} onClick={() => downloadDocument()}>
          Download HTML
        </button>
        <select aria-label="Format" value={format} onChange={(event) => setFormat(event.target.value)}>
          {["json", "csv", "html", "xlsx", "pdf"].map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <button
          className="btn"
          type="button"
          disabled={selected?.kind !== "comparison" || !selected.comparison_id}
          onClick={() => create.mutate()}
        >
          Generate
        </button>
      </div>
      {downloadError ? <p className="fault">{downloadError}</p> : null}
      <ul>
        {(reports.data ?? []).map((report) => (
          <li key={report.id}>
            {report.format} · {new Date(report.created_at).toLocaleString()}{" "}
            <button type="button" className="btn quiet" onClick={() => download(report)}>
              Download
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
