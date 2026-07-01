"""Exam Simulator (06-exam-simulator.md) — composes grade + review + progress into
one timed, multi-target engagement.

A session has targets and a deadline; each submission is two-signal graded AND its
report is rubric-scored; the final score combines findings + report, lists missed
paths, and generates a retake plan. Deterministic and offline (inject ``now`` and
``started_at`` in tests instead of relying on the wall clock).
"""

from __future__ import annotations

import threading
import time
import uuid

from .validator import ChallengeValidator


class ExamSimulator:
    DEFAULT_DURATION = 4 * 3600  # a 4h "MINI" engagement
    # MVP weighting folds methodology into findings; the full 45/15/40 with
    # attack-path-graph methodology (06-exam-simulator.md §4) is the target.
    FINDINGS_WEIGHT = 0.55
    REPORT_WEIGHT = 0.45
    PASS = 75

    def __init__(self, grader_state, reviewer, progress=None):
        self.state = grader_state
        self.reviewer = reviewer
        self.progress = progress
        self.sessions: dict = {}
        self._lock = threading.Lock()

    # --- lifecycle ----------------------------------------------------------
    def start_session(self, learner_id, lab_ids=None, duration_seconds=None, started_at=None):
        targets = [t for t in (lab_ids or list(self.state.labs)[:3]) if t in self.state.labs]
        started = float(started_at) if started_at is not None else time.time()
        duration = int(duration_seconds or self.DEFAULT_DURATION)
        sid = uuid.uuid4().hex[:12]
        session = {
            "session_id": sid,
            "learner_id": learner_id,
            "targets": targets,
            "started_at": started,
            "duration_seconds": duration,
            "deadline": started + duration,
            "results": {},
        }
        with self._lock:
            self.sessions[sid] = session
        return self._public(session)

    def _public(self, s):
        out = {k: s[k] for k in ("session_id", "learner_id", "targets",
                                 "started_at", "duration_seconds", "deadline")}
        out["submitted"] = list(s["results"].keys())
        return out

    def _session(self, session_id):
        s = self.sessions.get(session_id)
        if s is None:
            raise KeyError("no such exam session")
        return s

    # --- submission ---------------------------------------------------------
    def submit(self, session_id, lab_id, transcript, flag, finding=None, now=None):
        s = self._session(session_id)
        now = float(now) if now is not None else time.time()
        if now > s["deadline"]:
            return {"rejected": "deadline passed", "remaining": 0}
        if lab_id not in s["targets"]:
            return {"rejected": "lab is not part of this engagement"}

        manifest = self.state.labs[lab_id]
        grade = ChallengeValidator(manifest).grade(transcript, flag, self.state.seed, s["learner_id"])
        card = self.reviewer.review(finding or {}, transcript)
        if self.progress is not None:
            self.progress.record_attempt(s["learner_id"], manifest, grade)
            registry = getattr(self.state, "registry", None)
            if registry is not None and hasattr(self.progress, "award_badges"):
                self.progress.award_badges(s["learner_id"], registry)

        s["results"][lab_id] = {
            "passed": grade.passed,
            "signal_a": grade.signal_a,
            "signal_b": grade.signal_b,
            "report_total": card.total,
            "report_passed": card.passed,
        }
        return {
            "lab_id": lab_id,
            "lab_passed": grade.passed,
            "report_total": card.total,
            "remaining": round(s["deadline"] - now),
        }

    # --- scoring ------------------------------------------------------------
    def score(self, session_id, registry=None):
        s = self._session(session_id)
        targets, results = s["targets"], s["results"]
        n = len(targets) or 1
        passed = sum(1 for t in targets if results.get(t, {}).get("passed"))
        findings_frac = passed / n
        report_scores = [results[t]["report_total"] / 100 for t in targets if t in results]
        report_frac = sum(report_scores) / len(report_scores) if report_scores else 0.0
        total = round(100 * (self.FINDINGS_WEIGHT * findings_frac + self.REPORT_WEIGHT * report_frac))
        out = {
            "session_id": session_id,
            "score": total,
            "of": 100,
            "passed": total >= self.PASS,
            "findings": {"passed": passed, "of": n, "weight": self.FINDINGS_WEIGHT},
            "report": {"avg_pct": round(report_frac * 100), "weight": self.REPORT_WEIGHT},
            "missed_paths": [t for t in targets if not results.get(t, {}).get("passed")],
            "note": "MVP weighting folds methodology into findings; full 45/15/40 with "
                    "attack-path graphs is the target (06-exam-simulator.md).",
        }
        if registry is not None:
            out["retake_plan"] = self._retake_plan(s)
        return out

    def _retake_plan(self, s):
        plan = []
        for t in s["targets"]:
            r = s["results"].get(t)
            manifest = self.state.labs[t]
            owasp = (manifest.get("frameworks", {}).get("owasp") or ["?"])[0]
            if not r:
                plan.append({"lab": t, "skill": owasp, "reason": "not attempted",
                             "recommend": f"Attempt {t} — {manifest.get('title')}"})
            elif not r.get("passed"):
                plan.append({"lab": t, "skill": owasp, "reason": "not passed",
                             "recommend": f"Re-run {t} — {manifest.get('title')}"})
            elif r.get("report_total", 0) < 70:
                plan.append({"lab": t, "skill": "reporting", "reason": "weak report",
                             "recommend": f"Strengthen the {t} finding (impact/remediation/retest)"})
        return plan
