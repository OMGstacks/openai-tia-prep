"""Lab manifest load + schema validation — the binding rule (12-content-authoring.md).

Validates a lab manifest against the taxonomy registry so no lab can ship with an
unknown framework id, a ``detector_required`` that isn't in ``detector_catalog()``,
fewer than three defense variants, or a missing no-AI route. JSON is used (not the
blueprint's illustrative YAML) so validation stays stdlib-only.
"""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_FIELDS = [
    "id",
    "title",
    "ai300_module",
    "difficulty",
    "frameworks",
    "two_signal_grading",
    "defense_variants",
    "report_required",
    "ai_modes_allowed",
    "authorized_scope",
    "egress_policy",
    "reset_command",
]

DEFENSE_LEVELS = {f"D{i}" for i in range(9)}  # D0..D8
MIN_DEFENSE_VARIANTS = 3


def load(path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate(manifest: dict, registry) -> list:
    """Return a list of human-readable errors ([] == valid)."""
    errs = []

    for field_name in REQUIRED_FIELDS:
        if field_name not in manifest:
            errs.append(f"missing required field: {field_name}")

    # framework tags must resolve in the registry
    fw = manifest.get("frameworks", {}) or {}
    for oid in fw.get("owasp", []):
        if not registry.is_owasp(oid):
            errs.append(f"unknown OWASP id: {oid}")
    for tech in fw.get("atlas", []):
        if not registry.is_atlas(tech):
            errs.append(f"invalid ATLAS id form: {tech}")
    for aid in fw.get("agentic", []):
        if not registry.is_agentic(aid):
            errs.append(f"unknown agentic id: {aid}")

    # two-signal grading: detector must exist in detector_catalog()
    tsg = manifest.get("two_signal_grading", {}) or {}
    det = tsg.get("detector_required")
    if not det:
        errs.append("two_signal_grading.detector_required missing")
    elif not registry.is_detector(det):
        errs.append(f"detector_required not in detector_catalog(): {det}")
    if not tsg.get("evidence_tokens"):
        errs.append("two_signal_grading.evidence_tokens missing or empty")

    # defense variants: >= 3, all on the D0-D8 scale
    dv = manifest.get("defense_variants", []) or []
    if len(dv) < MIN_DEFENSE_VARIANTS:
        errs.append(f"defense_variants must list >= {MIN_DEFENSE_VARIANTS} levels")
    for level in dv:
        if level not in DEFENSE_LEVELS:
            errs.append(f"defense variant not on D0-D8 scale: {level}")

    # a no-AI route is mandatory (18-ai-use-policy-for-exam-mode.md)
    if "NO_AI" not in (manifest.get("ai_modes_allowed", []) or []):
        errs.append("ai_modes_allowed must include NO_AI")

    return errs


def validate_dir(labs_dir, registry) -> dict:
    """Validate every *.json manifest in a directory; {name: [errors]}."""
    report = {}
    for path in sorted(Path(labs_dir).glob("*.json")):
        try:
            report[path.name] = validate(load(path), registry)
        except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover - defensive
            report[path.name] = [f"could not load manifest: {exc}"]
    return report
