"""The two-signal ChallengeValidator (02-lab-range.md §A.2).

A lab passes only when BOTH signals fire:
  Signal A — the manifest's ``detector_required`` fires on the learner's
             transcript (via the reused engine), with the expected OWASP id.
  Signal B — the learner's evidence flag verifies (per-learner HMAC).

This defeats both regex false-negatives (an unfired detector fails A) and
learners gaming a sentinel string (a forged flag fails B).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import engine, flags


@dataclass
class GradeResult:
    lab_id: str
    signal_a: bool
    signal_b: bool
    passed: bool
    expected_detector: str
    expected_owasp: str
    fired_detectors: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Full internal/admin view — includes the answer key. Never serve to learners."""
        return {
            "lab_id": self.lab_id,
            "passed": self.passed,
            "signal_a_detector": self.signal_a,
            "signal_b_evidence": self.signal_b,
            "expected_detector": self.expected_detector,
            "expected_owasp": self.expected_owasp,
            "fired_detectors": self.fired_detectors,
            "findings": [f.as_row("learner") for f in self.findings],
            "notes": self.notes,
        }

    def public_feedback(self) -> dict:
        """Learner-facing view — reveals pass/fail and which signal is missing, but
        NOT the expected detector, OWASP id, or fired-detector list (the answer key)."""
        feedback = []
        if self.passed:
            feedback.append("Both signals satisfied — lab solved.")
        else:
            if not self.signal_a:
                feedback.append(
                    "Signal A (detection) not yet satisfied — your attack did not produce "
                    "the expected detectable behavior."
                )
            if not self.signal_b:
                feedback.append(
                    "Signal B (evidence) not verified — the evidence token did not match "
                    "your per-learner flag."
                )
        return {
            "lab_id": self.lab_id,
            "passed": self.passed,
            "signal_a": self.signal_a,
            "signal_b": self.signal_b,
            "feedback": feedback,
        }


class ChallengeValidator:
    """Grades one learner submission against one lab manifest."""

    # name -> owasp_id for every base detector, so a subtype finding can be mapped
    # back to the class its base detector belongs to.
    _DETECTOR_OWASP = {d["name"]: d["owasp_id"] for d in engine.detector_catalog()}

    def __init__(self, manifest: dict):
        self.manifest = manifest
        self.lab_id = manifest["id"]
        tsg = manifest["two_signal_grading"]
        self.expected_detector = tsg["detector_required"]
        owasp = (manifest.get("frameworks", {}) or {}).get("owasp", [])
        self.expected_owasp = owasp[0] if owasp else ""
        # The class the *detector* belongs to (may differ from the lab's framing —
        # e.g. L10 is framed LLM08 vector-weakness but graded by the LLM02 disclosure
        # detector). Signal A also accepts a finding in this class.
        self.detector_owasp = self._DETECTOR_OWASP.get(self.expected_detector, "")

    def grade(self, transcript, submitted_flag, server_seed, learner_id, attempt: int = 0) -> GradeResult:
        # --- Signal A: detector verdict over the transcript ---
        findings = []
        for event in transcript:
            findings.extend(engine.detect(event))
        fired = sorted({f.detector for f in findings})
        # Findings reliably carry owasp_id; some detectors (e.g. secret-leak) emit
        # subtype-specific Finding.detector names. Signal A passes when the named
        # detector fires, OR a finding matches the lab's framing OWASP class, OR a
        # finding matches the expected detector's own class (covers cross-framing
        # labs whose detector belongs to a different category than the lab framing).
        owasp_classes = {c for c in (self.expected_owasp, self.detector_owasp) if c}
        owasp_hit = any(f.owasp_id in owasp_classes for f in findings)
        signal_a = (self.expected_detector in fired) or owasp_hit

        notes = []
        if not signal_a:
            notes.append(
                f"Signal A: neither detector '{self.expected_detector}' nor a finding for "
                f"{self.expected_owasp or 'the target class'} fired (fired: {fired or 'none'})"
            )
        elif self.expected_detector not in fired:
            matched = sorted({f.owasp_id for f in findings if f.owasp_id in owasp_classes})
            notes.append(
                f"Signal A satisfied via OWASP class {matched} "
                f"(subtype detector(s): {fired})"
            )

        # --- Signal B: per-learner evidence flag ---
        signal_b = flags.verify_flag(server_seed, learner_id, self.lab_id, submitted_flag, attempt)
        if not signal_b:
            notes.append("Signal B: evidence flag did not verify")

        return GradeResult(
            lab_id=self.lab_id,
            signal_a=signal_a,
            signal_b=signal_b,
            passed=signal_a and signal_b,
            expected_detector=self.expected_detector,
            expected_owasp=self.expected_owasp,
            fired_detectors=fired,
            findings=findings,
            notes=notes,
        )
