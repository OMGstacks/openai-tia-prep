"""Progress & persistence engine (05-progress-engine.md) — SQLite, stdlib only.

Turns the stateless grader into a learning backend: every graded attempt updates
per-skill **mastery** (EMA on the shared taxonomy), awards **XP**, and feeds a
**weakness heatmap** and a heuristic **readiness** score. The mastery unit is the
same `owasp_id` / `atlas_technique` / `detector` tag the grader emits — the
shared-taxonomy invariant ([09b-reuse-map.md](09b-reuse-map.md)).
"""

from __future__ import annotations

import sqlite3
import threading

_SCHEMA = """
CREATE TABLE IF NOT EXISTS attempt (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  learner_id TEXT NOT NULL,
  lab_id     TEXT NOT NULL,
  passed     INTEGER NOT NULL,
  signal_a   INTEGER NOT NULL,
  signal_b   INTEGER NOT NULL,
  ts         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS skill_mastery (
  learner_id TEXT NOT NULL,
  skill_tag  TEXT NOT NULL,
  mastery    REAL NOT NULL DEFAULT 0,
  reps       INTEGER NOT NULL DEFAULT 0,
  last_seen  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (learner_id, skill_tag)
);
CREATE TABLE IF NOT EXISTS xp_ledger (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  learner_id TEXT NOT NULL,
  source     TEXT NOT NULL,
  points     INTEGER NOT NULL,
  ts         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_attempt_learner ON attempt(learner_id);
"""


class ProgressStore:
    ALPHA = 0.5  # EMA learning rate for a lab attempt (05-progress-engine.md §3)
    DIFFICULTY_XP = {"easy": 10, "medium": 20, "hard": 30}

    def __init__(self, db_path: str = ":memory:"):
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.executescript(_SCHEMA)
            self.conn.commit()

    @staticmethod
    def _skill_tags(manifest: dict) -> list:
        fw = manifest.get("frameworks", {}) or {}
        tags = list(fw.get("owasp", [])) + list(fw.get("atlas", [])) + list(fw.get("agentic", []))
        det = (manifest.get("two_signal_grading", {}) or {}).get("detector_required")
        if det:
            tags.append(det)
        return [t for t in tags if t]

    def record_attempt(self, learner_id: str, manifest: dict, result) -> dict:
        """Persist an attempt; update mastery for the lab's skill tags; award XP."""
        passed = 1 if result.passed else 0
        signal = 1.0 if result.passed else 0.0
        with self._lock:
            self.conn.execute(
                "INSERT INTO attempt(learner_id,lab_id,passed,signal_a,signal_b) VALUES(?,?,?,?,?)",
                (learner_id, manifest["id"], passed, int(result.signal_a), int(result.signal_b)),
            )
            for tag in self._skill_tags(manifest):
                row = self.conn.execute(
                    "SELECT mastery,reps FROM skill_mastery WHERE learner_id=? AND skill_tag=?",
                    (learner_id, tag),
                ).fetchone()
                old = row["mastery"] if row else 0.0
                reps = (row["reps"] if row else 0) + 1
                new = max(0.0, min(1.0, old + self.ALPHA * (signal - old)))
                self.conn.execute(
                    "INSERT INTO skill_mastery(learner_id,skill_tag,mastery,reps,last_seen) "
                    "VALUES(?,?,?,?,CURRENT_TIMESTAMP) "
                    "ON CONFLICT(learner_id,skill_tag) DO UPDATE SET "
                    "mastery=excluded.mastery, reps=excluded.reps, last_seen=CURRENT_TIMESTAMP",
                    (learner_id, tag, new, reps),
                )
            if result.passed:
                pts = self.DIFFICULTY_XP.get(manifest.get("difficulty", "medium"), 20)
                self.conn.execute(
                    "INSERT INTO xp_ledger(learner_id,source,points) VALUES(?,?,?)",
                    (learner_id, f"lab:{manifest['id']}", pts),
                )
            self.conn.commit()
        return {"learner_id": learner_id, "xp": self.xp(learner_id), "attempts": self.attempts(learner_id)}

    # --- reads --------------------------------------------------------------
    def mastery(self, learner_id: str) -> dict:
        rows = self.conn.execute(
            "SELECT skill_tag,mastery,reps FROM skill_mastery WHERE learner_id=?", (learner_id,)
        ).fetchall()
        return {r["skill_tag"]: {"mastery": round(r["mastery"], 4), "reps": r["reps"]} for r in rows}

    def xp(self, learner_id: str) -> int:
        r = self.conn.execute(
            "SELECT COALESCE(SUM(points),0) AS x FROM xp_ledger WHERE learner_id=?", (learner_id,)
        ).fetchone()
        return int(r["x"])

    def attempts(self, learner_id: str) -> dict:
        r = self.conn.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(passed),0) AS p FROM attempt WHERE learner_id=?",
            (learner_id,),
        ).fetchone()
        return {"total": int(r["c"]), "passed": int(r["p"])}

    def weakness_heatmap(self, learner_id: str, registry) -> dict:
        m = self.mastery(learner_id)
        return {
            oid: {"name": registry.owasp[oid], "mastery": m.get(oid, {}).get("mastery", 0.0)}
            for oid in registry.owasp
        }

    def readiness(self, learner_id: str, registry) -> dict:
        m = self.mastery(learner_id)
        scores = [m.get(oid, {}).get("mastery", 0.0) for oid in registry.owasp]
        avg = sum(scores) / len(scores)
        coverage = sum(1 for s in scores if s >= 0.5) / len(scores)
        return {
            "score": round(1000 * (0.7 * avg + 0.3 * coverage)),
            "of": 1000,
            "avg_owasp_mastery": round(avg, 3),
            "owasp_coverage": round(coverage, 3),
            "note": "heuristic MVP score; the full R0-R5 model is in 14-readiness-model.md",
        }

    def summary(self, learner_id: str, registry=None) -> dict:
        out = {
            "learner_id": learner_id,
            "attempts": self.attempts(learner_id),
            "xp": self.xp(learner_id),
            "mastery": self.mastery(learner_id),
        }
        if registry is not None:
            out["readiness"] = self.readiness(learner_id, registry)
            out["weakness_heatmap"] = self.weakness_heatmap(learner_id, registry)
        return out
