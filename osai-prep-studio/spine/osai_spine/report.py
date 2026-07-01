"""Report-Reviewer (08-reporting-and-canva.md, 19-business-impact-rubric.md).

Grades a learner's written finding against the business-impact rubric — deterministic
field/quality checks plus a classification check that **pre-fills the expected OWASP
id from the attack transcript** using the reused detectors (09b-reuse-map.md). No LLM:
an LLM-judge for prose quality slots in behind the same ``review`` seam later.

Rubric weights (19-business-impact-rubric.md §4):
  classification 15 · evidence 20 · reproduction 15 · business impact 15 ·
  root cause 10 · remediation 15 · retest 10   (sum = 100)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import engine

_OWASP_RE = re.compile(r"LLM\d{2}:2025")
_ATLAS_RE = re.compile(r"AML\.T(?:A)?\d{4}(?:\.\d{3})?")

WEIGHTS = {
    "classification": 15,
    "evidence": 20,
    "reproduction": 15,
    "business_impact": 15,
    "root_cause": 10,
    "remediation": 15,
    "retest": 10,
}
PASS_THRESHOLD = 70


def _items(value) -> list:
    """Normalize a field to a list of non-empty items (accept list / dict / str)."""
    if value is None:
        return []
    if isinstance(value, dict):
        out = []
        for v in value.values():
            out.extend(_items(v))
        return out
    if isinstance(value, str):
        return [ln.strip() for ln in re.split(r"[\n;]", value) if ln.strip()]
    if isinstance(value, (list, tuple)):
        return [x for x in value if x]
    return [value]


def _extract_owasp(*texts):
    for t in texts:
        m = _OWASP_RE.search(str(t or ""))
        if m:
            return m.group(0)
    return None


@dataclass
class ReportCard:
    total: int
    passed: bool
    dimensions: dict = field(default_factory=dict)
    classification: dict = field(default_factory=dict)
    invalid_ids: list = field(default_factory=list)
    feedback: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_threshold": PASS_THRESHOLD,
            "dimensions": self.dimensions,
            "classification": self.classification,
            "invalid_ids": self.invalid_ids,
            "feedback": self.feedback,
        }


class ReportReviewer:
    def __init__(self, registry):
        self.registry = registry

    def suggest_classification(self, transcript) -> dict | None:
        """Derive the expected classification from the transcript via the reused engine."""
        findings = []
        for event in transcript or []:
            findings.extend(engine.detect(event))
        if not findings:
            return None
        worst = max(findings, key=lambda f: engine.severity_rank(f.severity))
        return {"owasp_id": worst.owasp_id, "atlas": worst.atlas_technique,
                "severity": worst.severity, "detector": worst.detector}

    def review(self, finding: dict, transcript=None) -> ReportCard:
        scores, feedback = {}, []

        # --- classification (vs transcript-derived ground truth) ---
        learner_owasp = _extract_owasp(finding.get("owasp"), finding.get("owasp_id"))
        invalid = []
        for tid in _OWASP_RE.findall(" ".join(str(finding.get(k, "")) for k in ("owasp", "owasp_id"))):
            if not self.registry.is_owasp(tid):
                invalid.append(tid)
        suggested = self.suggest_classification(transcript) if transcript else None
        valid = bool(learner_owasp) and self.registry.is_owasp(learner_owasp)
        match = bool(suggested) and learner_owasp == suggested["owasp_id"]
        if not valid:
            scores["classification"] = 0.0
            feedback.append("classification: cite a valid OWASP LLM id (e.g. LLM01:2025).")
        elif suggested is None:
            scores["classification"] = 0.7  # valid but unverifiable without a transcript
        elif match:
            scores["classification"] = 1.0
        else:
            scores["classification"] = 0.4
            feedback.append(
                f"classification: you cited {learner_owasp} but the evidence points to "
                f"{suggested['owasp_id']} — re-check the category."
            )

        # --- evidence ---
        n_ev = len(_items(finding.get("evidence")))
        scores["evidence"] = 1.0 if n_ev >= 2 else 0.6 if n_ev == 1 else 0.0
        if n_ev == 0:
            feedback.append("evidence: attach reproducible evidence (transcript id, flag, screenshot, callback log).")

        # --- reproduction ---
        n_rep = len(_items(finding.get("reproduction")))
        scores["reproduction"] = 1.0 if n_rep >= 2 else 0.5 if n_rep == 1 else 0.0
        if n_rep == 0:
            feedback.append("reproduction: give step-by-step repro a reviewer can follow.")

        # --- business impact ---
        bi = finding.get("business_impact")
        rated = sum(1 for v in bi.values() if v) if isinstance(bi, dict) else 0
        scores["business_impact"] = 1.0 if rated >= 3 else 0.5 if rated >= 1 else 0.0
        if rated == 0:
            feedback.append("business_impact: rate confidentiality/integrity/availability/financial/regulatory impact.")

        # --- root cause ---
        scores["root_cause"] = 1.0 if _items(finding.get("root_cause")) else 0.0
        if not _items(finding.get("root_cause")):
            feedback.append("root_cause: explain the control that failed, not just what happened.")

        # --- remediation ---
        n_rem = len(_items(finding.get("remediation")))
        scores["remediation"] = 1.0 if n_rem >= 2 else 0.6 if n_rem == 1 else 0.0
        if n_rem == 0:
            feedback.append("remediation: propose immediate + strategic fixes.")

        # --- retest ---
        scores["retest"] = 1.0 if _items(finding.get("retest")) else 0.0
        if not _items(finding.get("retest")):
            feedback.append("retest: state how to confirm the fix closes the finding.")

        dimensions = {
            name: {"weight": WEIGHTS[name], "score": round(s, 3), "points": round(WEIGHTS[name] * s, 1)}
            for name, s in scores.items()
        }
        total = round(sum(d["points"] for d in dimensions.values()))
        return ReportCard(
            total=total,
            passed=total >= PASS_THRESHOLD,
            dimensions=dimensions,
            classification={
                "learner_owasp": learner_owasp,
                "suggested_owasp": suggested["owasp_id"] if suggested else None,
                "match": match,
                "valid": valid,
            },
            invalid_ids=invalid,
            feedback=feedback,
        )
