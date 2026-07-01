"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";
import { LearnerProvider, useLearner } from "@/lib/learner";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/labs", label: "Labs" },
  { href: "/tutor", label: "Tutor" },
  { href: "/progress", label: "Progress" },
  { href: "/exam", label: "Exam" },
  { href: "/capstone", label: "Capstone" },
];

function Header({ health, offline }: { health: Health | null; offline: boolean }) {
  const { learner, setLearner, authed, logout } = useLearner();
  const path = usePathname();
  const ai = health?.llm?.enabled ? "AI tutor ✓" : "AI tutor off";

  return (
    <header>
      <h1>
        OSAI Prep Studio <span className="sub">AI-300 / OSAI</span>
      </h1>
      <nav className="row" style={{ gap: 12, margin: 0 }}>
        {NAV.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            className={path === n.href ? undefined : "sub"}
            style={path === n.href ? { fontWeight: 600 } : undefined}
          >
            {n.label}
          </Link>
        ))}
      </nav>
      <span style={{ flex: 1 }} />
      {health?.auth_enabled ? (
        authed ? (
          <span className="row" style={{ gap: 8, margin: 0 }}>
            <span className="sub">
              signed in as <strong>{learner}</strong>
            </span>
            <button className="ghost" style={{ padding: "1px 8px" }} onClick={logout}>
              Sign out
            </button>
          </span>
        ) : (
          <Link href="/login" style={{ fontWeight: 600 }}>
            Sign in
          </Link>
        )
      ) : (
        <label>
          learner&nbsp;
          <input value={learner} size={12} onChange={(e) => setLearner(e.target.value)} />
        </label>
      )}
      <span className="sub">
        {offline ? "grader offline" : health ? `${health.labs.length} labs · ${ai}` : "connecting…"}
      </span>
    </header>
  );
}

function ConnectionBanner({ onRetry }: { onRetry: () => void }) {
  return (
    <div
      style={{
        background: "rgba(248,81,73,0.12)",
        borderBottom: "1px solid var(--bad)",
        color: "var(--ink)",
        padding: "8px 20px",
        fontSize: 13,
      }}
    >
      <strong style={{ color: "var(--bad)" }}>Can’t reach the grader.</strong> Start it with{" "}
      <code>uvicorn osai_spine.api:app --port 8077</code> (or set <code>OSAI_API_URL</code>), then{" "}
      <button className="ghost" style={{ padding: "1px 8px" }} onClick={onRetry}>
        retry
      </button>
      .
    </div>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [offline, setOffline] = useState(false);

  const checkHealth = () => {
    api
      .health()
      .then((h) => {
        setHealth(h);
        setOffline(false);
      })
      .catch(() => {
        setHealth(null);
        setOffline(true);
      });
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <LearnerProvider>
      <Header health={health} offline={offline} />
      {offline && <ConnectionBanner onRetry={checkHealth} />}
      <main>{children}</main>
    </LearnerProvider>
  );
}
