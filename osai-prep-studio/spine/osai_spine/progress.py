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
import time

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
CREATE TABLE IF NOT EXISTS flashcard (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  learner_id    TEXT NOT NULL,
  skill_tag     TEXT NOT NULL,
  prompt        TEXT NOT NULL,
  answer        TEXT NOT NULL,
  ef            REAL NOT NULL DEFAULT 2.5,
  interval_days INTEGER NOT NULL DEFAULT 0,
  reps          INTEGER NOT NULL DEFAULT 0,
  due_ts        REAL NOT NULL,
  created_ts    REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS badge (
  learner_id TEXT NOT NULL,
  code       TEXT NOT NULL,
  awarded_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (learner_id, code)
);
CREATE INDEX IF NOT EXISTS ix_attempt_learner ON attempt(learner_id);
CREATE INDEX IF NOT EXISTS ix_card_due ON flashcard(learner_id, due_ts);
"""

# Achievement badges (05-progress-engine.md §4 gamification). Each is awarded once,
# the first time its predicate holds; predicates read only the shared-taxonomy
# mastery/XP/readiness state so badges stay consistent with the rest of the engine.
BADGE_DEFS = [
    {"code": "first_blood", "title": "First Blood",
     "desc": "Pass your first lab."},
    {"code": "injection_specialist", "title": "Injection Specialist",
     "desc": "Reach 0.75 mastery in Prompt Injection (LLM01)."},
    {"code": "agentic_operator", "title": "Agentic Operator",
     "desc": "Reach 0.5 mastery on any OWASP Agentic (T1-T15) threat."},
    {"code": "privilege_breaker", "title": "Privilege Breaker",
     "desc": "Reach 0.5 mastery in Excessive Agency (LLM06)."},
    {"code": "centurion", "title": "Centurion",
     "desc": "Earn 100 XP."},
    {"code": "exam_ready", "title": "Exam Ready",
     "desc": "Reach a readiness score of 750/1000."},
]
_BADGE_META = {b["code"]: b for b in BADGE_DEFS}


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

    # --- badges & leaderboard (gamification) -------------------------------
    def _earned_codes(self, learner_id, registry) -> set:
        """The set of badge codes whose predicate currently holds for a learner."""
        m = self.mastery(learner_id)

        def mas(tag):
            return m.get(tag, {}).get("mastery", 0.0)

        codes = set()
        if self.attempts(learner_id)["passed"] >= 1:
            codes.add("first_blood")
        if mas("LLM01:2025") >= 0.75:
            codes.add("injection_specialist")
        if any(mas(t) >= 0.5 for t in registry.agentic):
            codes.add("agentic_operator")
        if mas("LLM06:2025") >= 0.5:
            codes.add("privilege_breaker")
        if self.xp(learner_id) >= 100:
            codes.add("centurion")
        if self.readiness(learner_id, registry)["score"] >= 750:
            codes.add("exam_ready")
        return codes

    def award_badges(self, learner_id, registry) -> list:
        """Award any newly-earned badges (idempotent). Returns the badges minted on
        this call, in catalog order, so a caller can surface 'you just earned X'."""
        earned = self._earned_codes(learner_id, registry)
        have = {
            r["code"] for r in self.conn.execute(
                "SELECT code FROM badge WHERE learner_id=?", (learner_id,)
            ).fetchall()
        }
        new = [b["code"] for b in BADGE_DEFS if b["code"] in earned and b["code"] not in have]
        if new:
            with self._lock:
                for code in new:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO badge(learner_id,code) VALUES(?,?)",
                        (learner_id, code),
                    )
                self.conn.commit()
        return [dict(_BADGE_META[c]) for c in new]

    def badges(self, learner_id) -> list:
        """All badges a learner has earned, in catalog order, with award timestamps."""
        have = {
            r["code"]: r["awarded_ts"] for r in self.conn.execute(
                "SELECT code,awarded_ts FROM badge WHERE learner_id=?", (learner_id,)
            ).fetchall()
        }
        return [dict(b, awarded_ts=have[b["code"]]) for b in BADGE_DEFS if b["code"] in have]

    def leaderboard(self, registry, limit: int = 10) -> list:
        """Rank every learner who has attempted a lab by XP, then labs passed, then
        readiness (06/05). Deterministic: ties break on learner_id."""
        learners = [
            r["learner_id"] for r in self.conn.execute(
                "SELECT DISTINCT learner_id FROM attempt"
            ).fetchall()
        ]
        rows = []
        for lid in learners:
            att = self.attempts(lid)
            rows.append({
                "learner_id": lid,
                "xp": self.xp(lid),
                "passed": att["passed"],
                "attempts": att["total"],
                "badges": len(self.badges(lid)),
                "readiness": self.readiness(lid, registry)["score"],
            })
        rows.sort(key=lambda r: (-r["xp"], -r["passed"], -r["readiness"], r["learner_id"]))
        rows = rows[: max(0, int(limit))]
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        return rows

    # --- spaced repetition (SM-2) ------------------------------------------
    def add_card(self, learner_id, skill_tag, prompt, answer, now=None) -> int:
        now = float(now) if now is not None else time.time()
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO flashcard(learner_id,skill_tag,prompt,answer,due_ts,created_ts) "
                "VALUES(?,?,?,?,?,?)",
                (learner_id, skill_tag, prompt, answer, now, now),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def seed_weakness_cards(self, learner_id, registry, now=None, threshold=0.5) -> list:
        """Create one flashcard per weak (mastery < threshold) OWASP category, skipping
        any category that already has a card. Drives deliberate practice on gaps."""
        now = float(now) if now is not None else time.time()
        m = self.mastery(learner_id)
        created = []
        for oid, name in registry.owasp.items():
            if m.get(oid, {}).get("mastery", 0.0) >= threshold:
                continue
            exists = self.conn.execute(
                "SELECT 1 FROM flashcard WHERE learner_id=? AND skill_tag=? LIMIT 1",
                (learner_id, oid),
            ).fetchone()
            if exists:
                continue
            created.append(self.add_card(learner_id, oid, f"Name and describe OWASP {oid}.", name, now))
        return created

    def due_cards(self, learner_id, now=None) -> list:
        now = float(now) if now is not None else time.time()
        rows = self.conn.execute(
            "SELECT id,skill_tag,prompt,answer,ef,interval_days,reps,due_ts FROM flashcard "
            "WHERE learner_id=? AND due_ts<=? ORDER BY due_ts",
            (learner_id, now),
        ).fetchall()
        return [dict(r) for r in rows]

    def review_card(self, card_id, grade, now=None) -> dict:
        """SM-2 update. ``grade`` 0-5; <3 lapses the card (interval reset to 1 day)."""
        now = float(now) if now is not None else time.time()
        grade = max(0, min(5, int(grade)))
        with self._lock:
            row = self.conn.execute(
                "SELECT ef,interval_days,reps FROM flashcard WHERE id=?", (card_id,)
            ).fetchone()
            if row is None:
                raise KeyError("no such flashcard")
            ef, interval, reps = row["ef"], row["interval_days"], row["reps"]
            if grade < 3:
                reps, interval = 0, 1
            else:
                reps += 1
                interval = 1 if reps == 1 else 6 if reps == 2 else max(1, round(interval * ef))
                ef = max(1.3, ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)))
            due = now + interval * 86400
            self.conn.execute(
                "UPDATE flashcard SET ef=?,interval_days=?,reps=?,due_ts=? WHERE id=?",
                (ef, interval, reps, due, card_id),
            )
            self.conn.commit()
        return {"card_id": card_id, "ef": round(ef, 3), "interval_days": interval, "reps": reps, "due_ts": due}

    def summary(self, learner_id: str, registry=None) -> dict:
        out = {
            "learner_id": learner_id,
            "attempts": self.attempts(learner_id),
            "xp": self.xp(learner_id),
            "mastery": self.mastery(learner_id),
            "badges": self.badges(learner_id),
        }
        if registry is not None:
            out["readiness"] = self.readiness(learner_id, registry)
            out["weakness_heatmap"] = self.weakness_heatmap(learner_id, registry)
        return out
