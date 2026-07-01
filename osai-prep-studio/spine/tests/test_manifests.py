from pathlib import Path

from osai_spine import manifest as m
from osai_spine.taxonomy import TaxonomyRegistry

LABS = Path(__file__).resolve().parents[1] / "labs"


def test_shipped_manifests_valid():
    reg = TaxonomyRegistry()
    report = m.validate_dir(LABS, reg)
    assert report, "expected shipped lab manifests"
    for name, errs in report.items():
        assert errs == [], f"{name}: {errs}"


def test_broken_manifest_is_rejected():
    reg = TaxonomyRegistry()
    bad = {
        "id": "Lbad",
        "title": "broken",
        "ai300_module": "M3",
        "difficulty": "easy",
        "frameworks": {"owasp": ["LLM99:2025"], "atlas": ["NOPE"], "agentic": ["T99"]},
        "two_signal_grading": {"detector_required": "not_a_detector", "evidence_tokens": []},
        "defense_variants": ["D0"],
        "report_required": True,
        "ai_modes_allowed": ["AI_ASSISTED"],
        "authorized_scope": ["x"],
        "egress_policy": "x",
        "reset_command": "x",
    }
    errs = " ".join(m.validate(bad, reg))
    assert "unknown OWASP id: LLM99:2025" in errs
    assert "invalid ATLAS id form: NOPE" in errs
    assert "unknown agentic id: T99" in errs
    assert "detector_required not in detector_catalog(): not_a_detector" in errs
    assert "evidence_tokens missing or empty" in errs
    assert ">= 3 levels" in errs
    assert "NO_AI" in errs
