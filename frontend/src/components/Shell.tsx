import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const links = [
  ["/", "Dashboard"],
  ["/servers", "Servers"],
  ["/import", "Import"],
  ["/credentials", "Credentials"],
  ["/runs", "Runs"],
  ["/reports", "Reports"],
] as const;

export function Shell({ children }: { children: ReactNode }) {
  const auth = useAuth();
  return (
    <div className="app-shell">
      <aside className="rail">
        <p className="eyebrow">Migration bench</p>
        <strong className="wordmark">HealthCheck</strong>
        <nav>
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              {label}
            </NavLink>
          ))}
        </nav>
        <button type="button" className="btn quiet" onClick={auth.logout}>
          Sign out
        </button>
      </aside>
      <div className="workspace">{children}</div>
    </div>
  );
}
