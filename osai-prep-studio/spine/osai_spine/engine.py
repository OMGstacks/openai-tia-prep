"""Bridge to the existing detection engine — reuse-first, no reimplementation.

The Phase-1 spine does NOT copy detector logic. It imports the tested engine at
``projects/llm-log-triage/src/detectors.py`` (by absolute path, independent of cwd)
and re-exports the few symbols the validator and taxonomy registry need. This is
the concrete realization of the reuse map (09b-reuse-map.md): one detection
engine, one taxonomy.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

# spine/osai_spine/engine.py -> parents: [0]=osai_spine [1]=spine [2]=osai-prep-studio [3]=repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
# Containers may relocate the engine; OSAI_DETECTORS_PATH overrides the in-repo path.
_DETECTORS_PATH = Path(
    os.environ.get("OSAI_DETECTORS_PATH")
    or (_REPO_ROOT / "projects" / "llm-log-triage" / "src" / "detectors.py")
)


def _load_engine():
    if not _DETECTORS_PATH.is_file():
        raise FileNotFoundError(
            f"detection engine not found at {_DETECTORS_PATH} — the spine reuses the "
            "existing llm-threat-triage detectors and cannot run without them."
        )
    spec = importlib.util.spec_from_file_location("osai_engine_detectors", _DETECTORS_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"could not load detection engine from {_DETECTORS_PATH}")
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so the module's @dataclass declarations can resolve
    # their own module via sys.modules (required with `from __future__ import
    # annotations`); otherwise dataclasses' _is_type lookup hits None.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_engine = _load_engine()

# Re-exported engine surface
detect = _engine.detect                      # (event: dict) -> list[Finding]
detector_catalog = _engine.detector_catalog  # () -> list[dict]
event_severity = _engine.event_severity      # (list[Finding]) -> str
severity_rank = _engine.severity_rank        # (str) -> int  (higher == worse)
Finding = _engine.Finding
ENGINE_PATH = str(_DETECTORS_PATH)
