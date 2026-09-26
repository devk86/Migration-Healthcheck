import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { api, getToken, setToken } from "../api/client";

interface AuthState {
  token: string | null;
  username: string;
  role: string;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(getToken());
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("");

  const value = useMemo<AuthState>(
    () => ({
      token,
      username,
      role,
      async login(nextUsername: string, password: string) {
        const result = await api<{ access_token: string; username: string; role: string }>(
          "/api/v1/auth/login",
          {
            method: "POST",
            body: JSON.stringify({ username: nextUsername, password }),
          },
        );
        setToken(result.access_token);
        setTokenState(result.access_token);
        setUsername(result.username);
        setRole(result.role);
      },
      logout() {
        setToken(null);
        setTokenState(null);
        setUsername("");
        setRole("");
      },
    }),
    [role, token, username],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("AuthProvider is missing");
  }
  return value;
}
