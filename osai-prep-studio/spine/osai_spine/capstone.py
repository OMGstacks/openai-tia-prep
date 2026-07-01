"""Blue-team triage capstone (L20, 02-lab-range.md) — the detection/reporting
showcase and the repo's home turf.

Unlike the attack labs (which two-signal grade an exploit), the capstone flips to the
defender: the learner triages a **mixed incident log** and their findings are scored
against ground truth produced by the **full reused detection engine** — OWASP
precision/recall plus whether they spotted the **session-escalation chain**
(injection -> realized impact). This mirrors the exam's ~50% report weight.

Stdlib only; the engine is the answer key, so the capstone stays consistent with the
shared taxonomy and never needs a hand-maintained label set.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import engine

DEFAULT_LOG = Path(__file__).resolve().parent.parent / "capstone" / "incident_log.json"
PASS = 70

# OWASP ids that, appearing after an injection, constitute a realized-impact chain.
_IMPACT = {"LLM02:2025", "LLM05:2025", "LLM06:2025"}


def load_incident_log(path=None) -> list:
    with open(path or DEFAULT_LOG, encoding="utf-8") as fh:
        return json.load(fh)


class TriageCapstone:
    """Scores a learner's triage of a mixed incident log against engine ground truth."""

    def __init__(self, log=None):
        self.log = log if log is not None else load_incident_log()
        self._truth = self._ground_truth()

    def _ground_truth(self) -> dict:
        per_event = []
        for idx, event in enumerate(self.log):
            ids = {f.owasp_id for f in engine.detect(event)}
            per_event.append((idx, ids))
        all_ids = set().union(*[ids for _, ids in per_event]) if per_event else set()
        inj_idx = [i for i, ids in per_event if "LLM01:2025" in ids]
        imp_idx = [i for i, ids in per_event if ids & _IMPACT]
        escalation = bool(inj_idx and imp_idx and min(inj_idx) < max(imp_idx))
        return {"owasp_ids": all_ids, "escalation": escalation}

    def public_brief(self) -> dict:
        """What the learner sees: the raw log + the task. NOT the answer key (no
        category labels, no counts)."""
        return {
            "events": self.log,
            "task": (
                "Triage this incident log. Report every OWASP LLM (2025) category "
                "present, state whether a session-escalation chain occurred "
                "(an injection leading to a realized impact), and write the chain up "
                "as a finding."
            ),
        }

    @staticmethod
    def _submitted_ids(submission) -> set:
        raw = (submission or {}).get("findings", []) or []
        ids = {(i.get("owasp_id") if isinstance(i, dict) else i) for i in raw}
        return {i for i in ids if i}

    def score(self, submission) -> dict:
        """Grade a submission {findings:[{owasp_id}|str], escalation_chain:bool}.
        F1 on the OWASP id set (recall matters — a missed finding is a real gap) plus
        the escalation judgment. Counts are returned (teaching signal) but NOT which
        specific ids were missed (no answer-key leak)."""
        submitted = self._submitted_ids(submission)
        truth = self._truth["owasp_ids"]
        tp = submitted & truth
        precision = len(tp) / len(submitted) if submitted else 0.0
        recall = len(tp) / len(truth) if truth else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        esc_correct = bool((submission or {}).get("escalation_chain")) == self._truth["escalation"]
        total = round(100 * (0.8 * f1 + 0.2 * (1.0 if esc_correct else 0.0)))
        return {
            "score": total,
            "of": 100,
            "passed": total >= PASS,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "escalation_correct": esc_correct,
            "counts": {
                "submitted": len(submitted),
                "correct": len(tp),
                "missed": len(truth - submitted),
                "false_positive": len(submitted - truth),
            },
        }
