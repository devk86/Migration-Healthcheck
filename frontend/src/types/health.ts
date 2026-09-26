export type CheckStatus = "ok" | "error";

export interface HealthResponse {
  status: "ok" | "degraded";
  service: string;
  version: string;
  environment: string;
  checks: Record<string, CheckStatus>;
}
