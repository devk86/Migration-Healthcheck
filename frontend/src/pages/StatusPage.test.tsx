import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StatusPage } from "./StatusPage";

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <StatusPage />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("StatusPage", () => {
  it("shows responding services when the lab is healthy", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          status: "ok",
          service: "migration-healthcheck",
          version: "0.1.0",
          environment: "test",
          checks: { database: "ok", redis: "ok" },
        }),
      }),
    );

    renderPage();

    expect(await screen.findByRole("heading", { name: "Lab is ready" })).toBeInTheDocument();
    expect(screen.getByText("database")).toBeInTheDocument();
    expect(screen.getAllByText("Responding")).toHaveLength(2);
  });

  it("explains when the API cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    renderPage();

    expect(await screen.findByRole("heading", { name: "API unreachable" })).toBeInTheDocument();
    expect(screen.getByText(/could not reach/i)).toBeInTheDocument();
  });
});
