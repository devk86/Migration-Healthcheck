export interface ComparisonRow {
  category: string;
  metric: string;
  pre_value: string;
  post_value: string;
  change: string;
  status: string;
  changed: boolean;
}

export type RowFilter = "all" | "changes" | "failures" | "warnings";

export function filterRows(rows: ComparisonRow[], mode: RowFilter): ComparisonRow[] {
  if (mode === "changes") {
    return rows.filter((row) => row.changed);
  }
  if (mode === "failures") {
    return rows.filter((row) => row.status === "FAIL");
  }
  if (mode === "warnings") {
    return rows.filter((row) => row.status === "WARN");
  }
  return rows;
}
