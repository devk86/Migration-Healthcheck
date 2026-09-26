import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Shell } from "./components/Shell";
import { ComparisonPage } from "./pages/ComparisonPage";
import { CredentialsPage } from "./pages/CredentialsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ImportPage } from "./pages/ImportPage";
import { LoginPage } from "./pages/LoginPage";
import { ReportsPage } from "./pages/ReportsPage";
import { RunDetailPage, RunsPage } from "./pages/RunPage";
import { ServerDetailPage } from "./pages/ServerDetailPage";
import { ServersPage } from "./pages/ServersPage";
import { StatusPage } from "./pages/StatusPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1 } },
});

function Private({ children }: { children: ReactNode }) {
  const auth = useAuth();
  if (!auth.token) {
    return <Navigate to="/login" replace />;
  }
  return <Shell>{children}</Shell>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/status" element={<StatusPage />} />
            <Route path="/" element={<Private><DashboardPage /></Private>} />
            <Route path="/servers" element={<Private><ServersPage /></Private>} />
            <Route path="/servers/:serverId" element={<Private><ServerDetailPage /></Private>} />
            <Route path="/import" element={<Private><ImportPage /></Private>} />
            <Route path="/credentials" element={<Private><CredentialsPage /></Private>} />
            <Route path="/runs" element={<Private><RunsPage /></Private>} />
            <Route path="/runs/:runId" element={<Private><RunDetailPage /></Private>} />
            <Route path="/comparisons/:comparisonId" element={<Private><ComparisonPage /></Private>} />
            <Route path="/reports" element={<Private><ReportsPage /></Private>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
