"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useLearner } from "@/lib/learner";
import type { ExamScore, ExamSession, ExamSubmitResult } from "@/lib/types";

const FINDING_TEMPLATE = JSON.stringify(
  {
    title: "Finding title",
    severity: "High",
    owasp: "LLM01:2025",
    evidence: ["transcript excerpt 1", "transcript excerpt 2"],
    reproduction: ["step 1", "step 2"],
    business_impact: { confidentiality: "High", integrity: "Medium", availability: "Low" },
    root_cause: ["the control that failed"],
    remediation: { immediate: ["fix a", "fix b"] },
    retest: ["how to verify the fix"],
  },
  null,
  2,
);

function mmss(secs: number): string {
  const s = Math.max(0, Math.floor(secs));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

export default function ExamRoom() {
  const { learner } = useLearner();
  const [labIds, setLabIds] = useState("");
  const [session, setSession] = useState<ExamSession | null>(null);
  const [now, setNow] = useState(() => Date.now() / 1000);
  const [attacks, setAttacks] = useState<Record<string, string>>({});
  const [flags, setFlags] = useState<Record<string, string>>({});
  const [findings, setFindings] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, ExamSubmitResult>>({});
  const [score, setScore] = useState<ExamScore | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    timer.current = setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  const start = async () => {
    const ids = labIds
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const s = await api.examStart(learner || "demo", ids.length ? ids : undefined);
    setSession(s);
    setResults({});
    setScore(null);
    const seed: Record<string, string> = {};
    s.targets.forEach((t) => (seed[t] = FINDING_TEMPLATE));
    setFindings(seed);
  };

  const submit = useCallback(
    async (lab: string) => {
      if (!session) return;
      let finding: Record<string, unknown> = {};
      try {
        finding = JSON.parse(findings[lab] || "{}");
      } catch {
        finding = {};
      }
      const transcript = [{ role: "user", source: "chat_ui", content: attacks[lab] || "" }];
      const r = await api.examSubmit(session.session_id, lab, transcript, flags[lab] || "", finding);
      setResults((prev) => ({ ...prev, [lab]: r }));
    },
    [session, attacks, flags, findings],
  );

  const finish = async () => {
    if (session) setScore(await api.examScore(session.session_id));
  };

  const remaining = session ? session.deadline - now : 0;
  const expired = session ? remaining <= 0 : false;

  return (
    <>
      <section className="panel">
        <h2>Exam simulator — start a timed engagement</h2>
        <div className="row">
          <input
            placeholder="lab ids (optional, comma-separated) — blank = default set"
            style={{ flex: 1 }}
            value={labIds}
            onChange={(e) => setLabIds(e.target.value)}
          />
          <button onClick={start}>Start</button>
        </div>
          {session && (
            <div className="row">
              <span className="pill">session {session.session_id.slice(0, 8)}</span>
              <span className={`pill ${expired ? "bad" : "ok"}`}>
                {expired ? "time up" : `time left ${mmss(remaining)}`}
              </span>
              <span className="muted">targets: {session.targets.join(", ")}</span>
              <button onClick={finish}>Finish &amp; score</button>
            </div>
          )}
        </section>

        {session &&
          session.targets.map((lab) => {
            const r = results[lab];
            return (
              <section className="panel" key={lab}>
                <h2>
                  Target {lab}
                  {r?.lab_passed ? " ✓" : ""}
                </h2>
                <textarea
                  placeholder={`Attack ${lab} — produce the detectable behavior`}
                  value={attacks[lab] || ""}
                  onChange={(e) => setAttacks((p) => ({ ...p, [lab]: e.target.value }))}
                />
                <div className="row">
                  <input
                    placeholder="evidence flag OSAI{...}"
                    style={{ flex: 1 }}
                    value={flags[lab] || ""}
                    onChange={(e) => setFlags((p) => ({ ...p, [lab]: e.target.value }))}
                  />
                </div>
                <label>finding (JSON — graded by the Report-Reviewer)</label>
                <textarea
                  style={{ minHeight: 120, fontFamily: "ui-monospace, monospace" }}
                  value={findings[lab] || ""}
                  onChange={(e) => setFindings((p) => ({ ...p, [lab]: e.target.value }))}
                />
                <div className="row">
                  <button onClick={() => submit(lab)} disabled={expired}>
                    Submit {lab}
                  </button>
                  {r && (
                    <span className="muted">
                      {r.rejected
                        ? `rejected: ${r.rejected}`
                        : `lab ${r.lab_passed ? "PASSED" : "not passed"} · report ${r.report_total}/100`}
                    </span>
                  )}
                </div>
              </section>
            );
          })}

        {score && (
          <section className="panel">
            <h2>Engagement score</h2>
            <div className="row">
              <span className={`pill ${score.passed ? "ok" : "bad"}`}>
                {score.passed ? "PASS" : "fail"} {score.score}/{score.of}
              </span>
              <span className="muted">
                findings {score.findings.passed}/{score.findings.of} (w {score.findings.weight}) · report{" "}
                {score.report.avg_pct}% (w {score.report.weight})
              </span>
            </div>
            {score.missed_paths.length > 0 && (
              <div className="muted">missed: {score.missed_paths.join(", ")}</div>
            )}
            {score.retake_plan && score.retake_plan.length > 0 && (
              <div className="out">
                {"Retake plan:\n"}
                {score.retake_plan.map((r) => `• [${r.skill}] ${r.recommend} (${r.reason})`).join("\n")}
              </div>
            )}
          </section>
        )}
    </>
  );
}
