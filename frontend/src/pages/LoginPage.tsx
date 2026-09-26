import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await auth.login(username, password);
      navigate("/");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign in failed.");
    }
  }

  return (
    <main className="console">
      <header className="mast">
        <p className="eyebrow">Migration bench</p>
        <h1>Sign in</h1>
        <p className="lede">The lab account is admin. Set a password before you leave this machine.</p>
      </header>
      <form className="panel" onSubmit={onSubmit}>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error ? <p className="fault">{error}</p> : null}
        <button className="btn" type="submit">
          Sign in
        </button>
      </form>
    </main>
  );
}
