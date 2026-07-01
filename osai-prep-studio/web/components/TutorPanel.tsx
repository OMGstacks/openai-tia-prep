"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { TutorAnswer } from "@/lib/types";

export default function TutorPanel() {
  const [query, setQuery] = useState("");
  const [ans, setAns] = useState<TutorAnswer | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const ask = async () => {
    setBusy(true);
    setErr(null);
    try {
      setAns(await api.tutorAsk(query));
    } catch (e) {
      setAns(null);
      setErr(e instanceof Error ? e.message : "request failed — is the grader running?");
    } finally {
      setBusy(false);
    }
  };

  const tag = ans?.refused
    ? "refused"
    : ans?.abstained
    ? "abstained"
    : ans?.generative
    ? "AI · grounded"
    : "extractive";

  return (
    <section className="panel">
      <h2>Tutor — grounded &amp; cited (abstains if unsure)</h2>
      <textarea
        placeholder="Ask: what is indirect prompt injection?"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="row">
        <button onClick={ask} disabled={busy}>
          {busy ? "asking…" : "Ask"}
        </button>
        <span className="muted">no source → no confident answer</span>
      </div>
      {err && <div className="out"><span className="pill bad">error</span> {err}</div>}
      {ans && (
        <div className="out">
          <span className={`pill ${ans.abstained || ans.refused ? "bad" : "ok"}`}>{tag}</span>{" "}
          {ans.answer}
          {ans.citations?.length ? (
            <>
              {"\n\nSources:\n"}
              {ans.citations.map((c) => `• ${c.source} — ${c.title} [${c.tier}]`).join("\n")}
            </>
          ) : null}
        </div>
      )}
    </section>
  );
}
