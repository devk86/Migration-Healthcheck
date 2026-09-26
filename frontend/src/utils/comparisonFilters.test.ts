import { describe, expect, it } from "vitest";
import { filterRows, type ComparisonRow } from "./comparisonFilters";

const rows: ComparisonRow[] = [
  {
    category: "disk",
    metric: "/",
    pre_value: "62%",
    post_value: "68%",
    change: "+6",
    status: "WARN",
    changed: true,
  },
  {
    category: "services",
    metric: "postgres",
    pre_value: "running",
    post_value: "stopped",
    change: "running → stopped",
    status: "FAIL",
    changed: true,
  },
  {
    category: "cpu",
    metric: "cores",
    pre_value: "4",
    post_value: "4",
    change: "0",
    status: "PASS",
    changed: false,
  },
];

describe("filterRows", () => {
  it("keeps every row", () => {
    expect(filterRows(rows, "all")).toHaveLength(3);
  });

  it("keeps changed rows", () => {
    expect(filterRows(rows, "changes").map((row) => row.metric)).toEqual(["/", "postgres"]);
  });

  it("keeps failures and warnings separately", () => {
    expect(filterRows(rows, "failures")).toHaveLength(1);
    expect(filterRows(rows, "warnings")[0]?.metric).toBe("/");
  });
});
