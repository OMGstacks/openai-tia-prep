"""The canonical taxonomy registry — the single source of truth for tags.

This is the mechanical enforcement of the shared-taxonomy invariant
(09b-reuse-map.md): every lesson/lab/question/finding tag must resolve to a
detector from the reused ``detector_catalog()``, an OWASP LLM (2025) id, an
ATLAS technique id, or an OWASP Agentic threat id (15-framework-version-ledger.md).
"""

from __future__ import annotations

import re

from . import engine

# Full OWASP LLM Top 10 (2025) — canonical (15-framework-version-ledger.md §3)
OWASP_LLM_2025 = {
    "LLM01:2025": "Prompt Injection",
    "LLM02:2025": "Sensitive Information Disclosure",
    "LLM03:2025": "Supply Chain",
    "LLM04:2025": "Data and Model Poisoning",
    "LLM05:2025": "Improper Output Handling",
    "LLM06:2025": "Excessive Agency",
    "LLM07:2025": "System Prompt Leakage",
    "LLM08:2025": "Vector and Embedding Weaknesses",
    "LLM09:2025": "Misinformation",
    "LLM10:2025": "Unbounded Consumption",
}

# OWASP Agentic threats T1-T15 (15-framework-version-ledger.md §3.1).
# mapping_confidence is medium until reconfirmed at ingest against the source.
OWASP_AGENTIC = {
    "T1": "Memory Poisoning",
    "T2": "Tool Misuse",
    "T3": "Privilege Compromise",
    "T4": "Resource Overload",
    "T5": "Cascading Hallucination",
    "T6": "Intent Breaking & Goal Manipulation",
    "T7": "Misaligned & Deceptive Behaviors",
    "T8": "Repudiation & Untraceability",
    "T9": "Identity Spoofing & Impersonation",
    "T10": "Overwhelming Human-in-the-Loop",
    "T11": "Unexpected RCE & Code Attacks",
    "T12": "Agent Communication Poisoning",
    "T13": "Rogue Agents in Multi-Agent Systems",
    "T14": "Human Attacks on Multi-Agent Systems",
    "T15": "Human Manipulation",
}

# ATLAS is a large external framework; validate by canonical id FORM rather than
# enumerating it (e.g. AML.T0051.001, AML.TA0002).
_ATLAS_RE = re.compile(r"^AML\.T(A)?\d{4}(\.\d{3})?$")


class TaxonomyRegistry:
    """Validates tags against the reused catalog + the framework ledgers."""

    def __init__(self):
        self.catalog = engine.detector_catalog()
        self.detectors = {d["name"]: d for d in self.catalog}
        self.detector_owasp = {d["name"]: d["owasp_id"] for d in self.catalog}
        self.owasp = dict(OWASP_LLM_2025)
        self.agentic = dict(OWASP_AGENTIC)

    # --- membership tests --------------------------------------------------
    def is_detector(self, name: str) -> bool:
        return name in self.detectors

    def is_owasp(self, oid: str) -> bool:
        return oid in self.owasp

    def is_atlas(self, technique: str) -> bool:
        return bool(_ATLAS_RE.match(technique or ""))

    def is_agentic(self, tid: str) -> bool:
        return tid in self.agentic

    def is_valid_tag(self, tag: str) -> bool:
        return (
            self.is_detector(tag)
            or self.is_owasp(tag)
            or self.is_atlas(tag)
            or self.is_agentic(tag)
        )

    def invalid_tags(self, tags) -> list:
        return [t for t in tags if not self.is_valid_tag(t)]

    # --- convenience -------------------------------------------------------
    def detector_names(self) -> list:
        return sorted(self.detectors)

    def owasp_for_detector(self, name: str):
        return self.detector_owasp.get(name)
