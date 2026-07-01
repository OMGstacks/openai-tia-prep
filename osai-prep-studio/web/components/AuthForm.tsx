"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useLearner } from "@/lib/learner";

export default function AuthForm() {
  const { login } = useLearner();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = mode === "login" ? await api.login(username, password) : await api.register(username, password);
      login(res.learner_id, res.token);
      router.push("/");
    } catch (e) {
      setError(
        mode === "login"
          ? "invalid credentials (or auth is disabled on the server)"
          : "could not register — username taken or password too short (min 8)",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel" style={{ maxWidth: 420 }}>
      <h2>{mode === "login" ? "Sign in" : "Create an account"}</h2>
      <div className="row">
        <button className={mode === "login" ? "" : "ghost"} onClick={() => setMode("login")}>
          Sign in
        </button>
        <button className={mode === "register" ? "" : "ghost"} onClick={() => setMode("register")}>
          Register
        </button>
      </div>
      <div className="row">
        <input
          placeholder="username"
          style={{ flex: 1 }}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
      </div>
      <div className="row">
        <input
          type="password"
          placeholder="password (min 8 chars)"
          style={{ flex: 1 }}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
      </div>
      <div className="row">
        <button onClick={submit} disabled={busy || !username || !password}>
          {busy ? "…" : mode === "login" ? "Sign in" : "Register"}
        </button>
        {error && <span className="pill bad">{error}</span>}
      </div>
      <div className="muted" style={{ fontSize: 11 }}>
        Auth is optional (server <code>OSAI_AUTH=1</code>). When enabled, the server derives
        your learner id from the signed token — you can only act as yourself.
      </div>
    </section>
  );
}
