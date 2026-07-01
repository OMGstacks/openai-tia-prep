# Business-Impact Rubric

> Purpose: Turn technical exploitation into executive-grade reporting — the half of the AI red-team job (and the OSAI exam) most prep ignores. Defines the finding template, severity model, and report scoring. Integrates the uploaded addendum; consumed by the Report-Reviewer ([08-reporting-and-canva.md](08-reporting-and-canva.md)).

## 1. What a professional finding answers

What was compromised · why the control failed · who could abuse it · what business process is affected · what to fix first · how to retest. A finding that stops at "I got the flag" is not a finding.

## 2. Finding template

```yaml
finding:
  title: "Indirect Prompt Injection Allows RAG Assistant to Leak Confidential HR Policy Snippets"
  severity: "High"          # see §3
  confidence: "High"
  affected_assets: ["MegacorpAI HR Assistant", "vector index: hr_docs"]
  owasp: "LLM01:2025 Prompt Injection"
  atlas: "AML.T0051.001"
  nist_ai_rmf: { functions: ["MAP","MEASURE","MANAGE"] }
  business_impact:
    confidentiality: "High"
    integrity: "Medium"
    availability: "Low"
    financial: "Medium"
    regulatory: "Medium"
    operational: "Medium"
  evidence: ["transcript_id", "flag_id", "screenshot_path", "callback_log_path"]
  root_cause:
    - "Retrieved documents were treated as instructions instead of untrusted data."
    - "Assistant lacked source-level access control and instruction-hierarchy enforcement."
  remediation:
    immediate: ["block retrieved content from issuing instructions", "source allowlist + document-level access control", "output validation for sensitive-data classes"]
    strategic: ["implement a RAG threat model", "add adversarial retrieval evals to CI", "log retrieval source ids + policy decisions"]
  retest: ["re-run L02 attack graph N1-N7", "confirm no planted-secret disclosure", "confirm audit log records the blocked instruction"]
```

The `owasp`/`atlas`/`severity` fields are pre-filled by the reused `Finding` classifier ([09b-reuse-map.md](09b-reuse-map.md)); the learner writes the impact, root cause, remediation, and retest.

## 3. Severity model (AI red-team definitions)

| Severity | Definition |
|---|---|
| Critical | Unauthorized high-impact action, credential compromise, broad data exfiltration, or persistent compromise of AI/infrastructure |
| High | Sensitive-data exposure, agent/tool abuse, privilege-boundary bypass, or reliable manipulation of business-critical output |
| Medium | Limited leakage, unreliable exploitation, local-only impact, or contained policy bypass |
| Low | Observable weakness with unrealistic preconditions or minimal business impact |
| Informational | Useful hardening observation, no direct exploit path |

## 4. Report scoring (the rubric)

| Dimension | Weight |
|---|---:|
| Correct vulnerability classification | 15% |
| Evidence quality | 20% |
| Reproduction clarity | 15% |
| Business impact | 15% |
| Root cause | 10% |
| Remediation | 15% |
| Retest plan | 10% |

This rubric drives the Report-Reviewer's score, the exam simulator's 40% report component ([06-exam-simulator.md](06-exam-simulator.md)), and the R5 readiness gate ([14-readiness-model.md](14-readiness-model.md)). Its lineage is the existing `../docs/playbook/analyst-runbook.md` severity rubric and the case-study exemplar.

## Cross-references
[06-exam-simulator.md](06-exam-simulator.md) · [08-reporting-and-canva.md](08-reporting-and-canva.md) · [09b-reuse-map.md](09b-reuse-map.md) · [14-readiness-model.md](14-readiness-model.md)
