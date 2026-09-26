import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { filterRows, type ComparisonRow, type RowFilter } from "../utils/comparisonFilters";

interface Comparison {
  id: string;
  server_id: string;
  overall_status: string;
  results: ComparisonRow[];
}

export function ComparisonPage() {
  const { comparisonId = "" } = useParams();
  const [mode, setMode] = useState<RowFilter>("all");
  const comparison = useQuery({
    queryKey: ["comparison", comparisonId],
    queryFn: () => api<Comparison>(`/api/v1/comparisons/${comparisonId}`),
  });
  const rows = filterRows(comparison.data?.results ?? [], mode);
  return (
    <section>
      <h1>Comparison · {comparison.data?.overall_status ?? ""}</h1>
      <div className="actions" role="group" aria-label="Row filters">
        {(
          [
            ["all", "All"],
            ["changes", "Changes only"],
            ["failures", "Failures"],
            ["warnings", "Warnings"],
          ] as const
        ).map(([value, label]) => (
          <button key={value} type="button" className="btn" onClick={() => setMode(value)}>
            {label}
          </button>
        ))}
      </div>
      <table className="grid">
        <thead>
          <tr>
            <th>Metric</th>
            <th>PRE</th>
            <th>POST</th>
            <th>Change</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.category}-${row.metric}`}>
              <td>
                {row.category} {row.metric}
              </td>
              <td>{row.pre_value}</td>
              <td>{row.post_value}</td>
              <td>{row.change}</td>
              <td>{row.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
