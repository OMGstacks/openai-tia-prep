"""OSAI Prep Studio — Phase-1 spine.

The reuse-first core the whole product hangs on (10-mvp-roadmap.md):
  * engine     — bridge to the existing llm-threat-triage detection engine
  * taxonomy   — the canonical tag registry (the shared-taxonomy invariant)
  * flags      — per-learner HMAC evidence flags (Signal B)
  * manifest   — lab-manifest load + schema validation (the binding rule)
  * validator  — the two-signal ChallengeValidator

Design-faithful to the blueprint in ../.. ; stdlib-only to keep the repo's
zero-dependency CI green. Lab manifests are JSON (the blueprint shows YAML for
readability; JSON needs no third-party parser).
"""

__all__ = ["engine", "taxonomy", "flags", "manifest", "validator"]
__version__ = "0.1.0"
