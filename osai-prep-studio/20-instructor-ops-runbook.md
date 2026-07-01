# Instructor Operations Runbook

> Purpose: Keep the studio current and safe over time — a monthly update ritual that defeats drift, and an incident response for broken labs. Integrates the uploaded addendum.

## 1. Monthly update ritual

AI-300/OSAI is new and evolving, and the frameworks move. Once a month, content-governance runs:

1. Re-check the **OffSec AI-300 course page**.
2. Re-check the **OffSec AI-300 (course) FAQ**.
3. Re-check the **OSAI Exam FAQ**.
4. Re-check the **OSAI Exam Guide** (watch for `pending` claims being finalized — esp. report window, AI-use guidelines, pass threshold).
5. Re-check **OWASP GenAI / LLM Top 10**.
6. Re-check **OWASP Agentic AI** resources.
7. Re-check **MITRE ATLAS** version and technique set.
8. Re-check **NIST AI RMF / GenAI Profile** updates.
9. Run `framework_ledger_diff` ([15-framework-version-ledger.md](15-framework-version-ledger.md)).
10. Run the **tutor gold-set regression** ([04-evaluation-harness.md](04-evaluation-harness.md)).
11. Regenerate affected flashcards and questions.
12. Publish a **changelog** entry (what changed, which claim ledger ids moved status, migration notes).

Outputs feed two ledgers: the **claim ledger** (`exam-claims.yml`, [00b-exam-blueprint.md](00b-exam-blueprint.md)) for OffSec/exam facts, and the **framework ledger** for OWASP/ATLAS/NIST. Any `pending → confirmed` transition unlocks the corresponding gated product behavior (e.g., a real report-window value, finalized `EXAM_CURRENT` AI rules).

## 2. Broken-lab response

```yaml
broken_lab_response:
  severity_1:
    definition: "Lab cannot start, cannot reset, or exposes unsafe egress."
    action: "Disable lab immediately; open hotfix issue; notify cohort."
  severity_2:
    definition: "Lab starts but grader produces false pass/fail."
    action: "Disable scoring; allow manual review; flag affected attempts."
  severity_3:
    definition: "Hint, UI, or report-template issue."
    action: "Keep lab active; fix in next patch."
```

S1/S2 map to the platform incident tiers in [13-platform-threat-model.md](13-platform-threat-model.md). The studio triages its own logs with the reused `../projects/llm-log-triage/` engine.

## 3. Cadence summary

| Cadence | Activity |
|---|---|
| On every content PR | taxonomy-tag + framework-ledger + lab-manifest + gold-set CI ([12-content-authoring.md](12-content-authoring.md)) |
| Weekly | review failed-lab analytics + tutor abstention/refusal compliance |
| Monthly | the source/framework update ritual (§1) |
| On OffSec spec change | edit `exam_config.yml` + claim ledger; rerun gold-set; changelog |

## Cross-references
[00b-exam-blueprint.md](00b-exam-blueprint.md) · [04-evaluation-harness.md](04-evaluation-harness.md) · [12-content-authoring.md](12-content-authoring.md) · [13-platform-threat-model.md](13-platform-threat-model.md) · [15-framework-version-ledger.md](15-framework-version-ledger.md)

## Sources
OffSec AI-300: <https://www.offsec.com/courses/ai-300/> · OSAI Exam FAQ: <https://help.offsec.com/hc/en-us/articles/46669767163156-OSAI-Advanced-AI-Red-Teaming-Exam-FAQ> · OWASP LLM Top 10: <https://genai.owasp.org/llm-top-10/> · MITRE ATLAS: <https://atlas.mitre.org/> · NIST AI RMF: <https://www.nist.gov/itl/ai-risk-management-framework>
