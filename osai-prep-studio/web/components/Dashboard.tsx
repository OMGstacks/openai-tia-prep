"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";
import LabsPanel from "./LabsPanel";
import TutorPanel from "./TutorPanel";
import ProgressPanel from "./ProgressPanel";
import LeaderboardPanel from "./LeaderboardPanel";
import FlashcardsPanel from "./FlashcardsPanel";
import CapstonePanel from "./CapstonePanel";

export default function Dashboard() {
  const [learner, setLearner] = useState("demo");
  const [health, setHealth] = useState<Health | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? window.localStorage.getItem("osai_learner") : null;
    if (saved) setLearner(saved);
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  const onLearnerChange = (v: string) => {
    setLearner(v);
    if (typeof window !== "undefined") window.localStorage.setItem("osai_learner", v);
  };

  const bumpRefresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  const aiLabel = health?.llm?.enabled ? "AI tutor ✓" : "AI tutor off (offline mode)";

  return (
    <>
      <header>
        <h1>
          OSAI Prep Studio <span className="sub">AI-300 / OSAI training range</span>
        </h1>
        <span className="sub">authorized-lab-only</span>
        <span style={{ flex: 1 }} />
        <label>
          learner&nbsp;
          <input value={learner} size={12} onChange={(e) => onLearnerChange(e.target.value)} />
        </label>
        <span className="sub">
          {health
            ? `engine ✓ · ${health.labs.length} labs · corpus ${health.tutor_corpus_chunks} · ${aiLabel}`
            : "connecting to grader…"}
        </span>
      </header>

      <main>
        <LabsPanel learner={learner} onGraded={bumpRefresh} />
        <TutorPanel />
        <ProgressPanel learner={learner} refreshKey={refreshKey} />
        <FlashcardsPanel learner={learner} refreshKey={refreshKey} />
        <LeaderboardPanel refreshKey={refreshKey} />
        <CapstonePanel />
      </main>
    </>
  );
}
