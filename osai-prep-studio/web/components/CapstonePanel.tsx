"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { CapstoneBrief, CapstoneScore } from "@/lib/types";

const OWASP = [
  "LLM01:2025",
  "LLM02:2025",
  "LLM03:2025",
  "LLM04:2025",
  "LLM05:2025",
  "LLM06:2025",
  "LLM07:2025",
  "LLM08:2025",
  "LLM09:2025",
  "LLM10:2025",
];

export default function CapstonePanel() {
  const { data: brief, loading, error } = useApi<CapstoneBrief>(() => api.capstone(), []);
  const [picked, setPicked] = useState<Record<string, boolean>>({});
  const [escalation, setEscalation] = useState(false);
  const [score, setScore] = useState<CapstoneScore | null>(null);

  const toggle = (id: string) => setPicked((p) => ({ ...p, [id]: !p[id] }));

  const submit = async () => {
    const findings = OWASP.filter((id) => picked[id]).map((id) => ({ owasp_id: id }));
    try {
      setScore(await api.capstoneScore(findings, escalation));
    } catch {
      setScore(null);
    }
  };

  return (
    <section className="panel">
      <h2>Blue-team capstone (L20) — triage the incident log</h2>
      {brief ? (
        <>
          <div className="muted" style={{ marginBottom: 6 }}>
            {brief.task}
          </div>
          <div className="out" style={{ maxHeight: 140 }}>
            {brief.events
              .map((e, i) => `${i + 1}. [${e.role}/${e.source}] ${e.content}`)
              .join("\n")}
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            {OWASP.map((id) => (
              <label key={id} style={{ color: "var(--ink)" }}>
                <input type="checkbox" checked={!!picked[id]} onChange={() => toggle(id)} />
                &nbsp;{id.replace(":2025", "")}
              </label>
            ))}
          </div>
          <div className="row">
            <label style={{ color: "var(--ink)" }}>
              <input
                type="checkbox"
                checked={escalation}
                onChange={(e) => setEscalation(e.target.checked)}
              />
              &nbsp;session-escalation chain present
            </label>
            <button onClick={submit}>Score triage</button>
          </div>
          {score && (
            <div className="out">
              <span className={`pill ${score.passed ? "ok" : "bad"}`}>
                {score.passed ? "PASS" : "fail"} {score.score}/{score.of}
              </span>{" "}
              precision {score.precision} · recall {score.recall} · f1 {score.f1}
              {"\n"}
              escalation {score.escalation_correct ? "✓" : "✗"} · missed {score.counts.missed} ·
              false-positive {score.counts.false_positive}
            </div>
          )}
        </>
      ) : (
        <span className="muted">{loading ? "loading…" : error ? "grader error" : "unavailable"}</span>
      )}
    </section>
  );
}
