"""L20 blue-team triage capstone: ground truth from the reused engine, scoring, and
the no-answer-key public brief."""

from osai_spine.capstone import TriageCapstone, load_incident_log


def test_ground_truth_from_engine():
    cap = TriageCapstone()
    # the seeded incident log realizes an injection -> impact escalation across five
    # OWASP categories, all derived from the engine (not a hand-kept label set)
    assert cap._truth["owasp_ids"] == {
        "LLM01:2025", "LLM02:2025", "LLM05:2025", "LLM06:2025", "LLM07:2025"
    }
    assert cap._truth["escalation"] is True


def test_perfect_triage_scores_100():
    cap = TriageCapstone()
    sub = {"findings": [{"owasp_id": i} for i in cap._truth["owasp_ids"]],
           "escalation_chain": True}
    r = cap.score(sub)
    assert r["score"] == 100 and r["passed"] is True
    assert r["counts"]["missed"] == 0 and r["counts"]["false_positive"] == 0


def test_partial_triage_fails_and_reports_misses():
    cap = TriageCapstone()
    sub = {"findings": ["LLM01:2025", "LLM02:2025"], "escalation_chain": False}
    r = cap.score(sub)
    assert r["passed"] is False
    assert r["recall"] < 1.0 and r["counts"]["missed"] == 3
    assert r["escalation_correct"] is False


def test_false_positive_lowers_precision():
    cap = TriageCapstone()
    sub = {"findings": [{"owasp_id": i} for i in cap._truth["owasp_ids"]] + ["LLM10:2025"],
           "escalation_chain": True}
    r = cap.score(sub)
    assert r["precision"] < 1.0 and r["counts"]["false_positive"] == 1


def test_public_brief_has_no_answer_key():
    cap = TriageCapstone()
    brief = cap.public_brief()
    assert brief["events"] == load_incident_log()
    assert "task" in brief
    # the brief must not leak the ground-truth labels, counts, or escalation verdict
    assert "owasp_ids" not in brief and "escalation" not in brief
    assert "expected_finding_count" not in brief
