import type { HealthResponse } from "../types/health";

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/v1/health");
  if (!response.ok && response.status !== 503) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}
