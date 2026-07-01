"use client";

import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { useLearner } from "@/lib/learner";
import type { Progress } from "@/lib/types";

export default function ProgressPanel() {
  const { learner } = useLearner();
  const { data: p, loading, error, reload } = useApi<Progress>(
    () => api.progress(learner || "demo"),
    [learner],
  );

  const heatmap = p?.weakness_heatmap ? Object.entries(p.weakness_heatmap) : [];

  return (
    <section className="panel">
      <h2>Progress &amp; readiness</h2>
      <div className="row">
        <button className="ghost" onClick={reload}>
          Refresh
        </button>
        {loading && <span className="muted">loading…</span>}
        {error && <span className="pill bad">grader error</span>}
        {p && !loading && (
          <span className="muted">
            xp {p.xp} · attempts {p.attempts.passed}/{p.attempts.total}
          </span>
        )}
      </div>
      <div className="row">
        <strong>Readiness</strong>&nbsp;
        <span className="pill">{p?.readiness ? `${p.readiness.score}/${p.readiness.of}` : "–"}</span>
      </div>
      <div>
        {heatmap.map(([id, v]) => (
          <div className="row" style={{ gap: 6 }} key={id}>
            <span style={{ width: 78 }} className="muted">
              {id.replace(":2025", "")}
            </span>
            <div className="bar">
              <span style={{ width: `${Math.round((v.mastery || 0) * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="row" style={{ marginTop: 8 }}>
        {(p?.badges || []).map((b) => (
          <span className="pill ok" key={b.code} title={b.desc}>
            ★ {b.title}
          </span>
        ))}
        {p && !p.badges.length && <span className="muted">no badges yet — pass a lab to earn First Blood</span>}
      </div>
    </section>
  );
}
