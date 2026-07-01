"use client";

import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { LeaderboardRow } from "@/lib/types";

export default function LeaderboardPanel() {
  const { data, loading, error, reload } = useApi<LeaderboardRow[]>(() => api.leaderboard(), []);
  const rows = data ?? [];

  return (
    <section className="panel">
      <h2>Leaderboard</h2>
      <div className="row">
        <button className="ghost" onClick={reload}>
          Refresh
        </button>
        {loading && <span className="muted">loading…</span>}
        {error && <span className="pill bad">grader error</span>}
      </div>
      {rows.length ? (
        rows.map((r) => (
          <div className="row" style={{ gap: 6 }} key={r.learner_id}>
            <span className="muted" style={{ width: 26 }}>
              #{r.rank}
            </span>
            <strong style={{ flex: 1 }}>{r.learner_id}</strong>
            <span className="pill">xp {r.xp}</span>
            <span className="pill">{r.passed} passed</span>
            <span className="pill">{r.badges}★</span>
          </div>
        ))
      ) : (
        <span className="muted">
          {loading ? "" : "no entries yet — pass a lab to appear here"}
        </span>
      )}
    </section>
  );
}
