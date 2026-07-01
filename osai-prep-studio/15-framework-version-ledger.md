# Framework Version Ledger

> Purpose: Treat OWASP / ATLAS / NIST / agentic mappings as **versioned data, not static copy**, so framework drift never silently corrupts lessons, labs, questions, or report findings. Integrates the uploaded addendum.

## 1. Why this exists

AI security frameworks move fast (OWASP refreshes the LLM Top 10; MITRE ATLAS adds techniques; NIST updates profiles). If mappings are hard-coded prose, a single upstream change silently makes the whole product wrong. The ledger makes every framework a registered, versioned source with an owner and an update policy, enforced in CI.

## 2. Framework source schema

```yaml
framework_source:
  id: "owasp-llm-top-10-2025"
  name: "OWASP Top 10 for LLM Applications and Generative AI"
  version: "2025"
  authority: "OWASP GenAI Security Project"
  url: "https://genai.owasp.org/llm-top-10/"
  retrieved_at: "2026-06-30"
  status: "active"             # active | deprecated
  update_frequency: "monthly-check"
  owner: "content-governance"
  breaking_change_policy: "open PR with migration map"
```

## 3. Canonical OWASP LLM Top 10 (2025)

Use these exact ids/names unless a later OWASP source supersedes them:

| ID | Name |
|---|---|
| `LLM01:2025` | Prompt Injection |
| `LLM02:2025` | Sensitive Information Disclosure |
| `LLM03:2025` | Supply Chain |
| `LLM04:2025` | Data and Model Poisoning |
| `LLM05:2025` | Improper Output Handling |
| `LLM06:2025` | Excessive Agency |
| `LLM07:2025` | System Prompt Leakage |
| `LLM08:2025` | Vector and Embedding Weaknesses |
| `LLM09:2025` | Misinformation |
| `LLM10:2025` | Unbounded Consumption |

Registered companions: **OWASP Agentic AI — Threats and Mitigations**, **MITRE ATLAS** (record the matrix version, e.g. v5.x, at ingest), **NIST AI RMF 1.0** + **AI 600-1 GenAI Profile** (12 risk categories), **NVIDIA AI Kill Chain**.

### 3.1 Canonical OWASP Agentic threats (T1–T15) → lab mapping

From OWASP **Agentic AI — Threats and Mitigations** (Agentic Security Initiative). IDs/names are pinned here so agentic coverage is **CI-verifiable** (the binding rule, [12-content-authoring.md](12-content-authoring.md)); `mapping_confidence` is `medium` until reconfirmed at ingest against the source (the exact T-numbering should be re-verified during the monthly ritual, [20-instructor-ops-runbook.md](20-instructor-ops-runbook.md)). "Roadmap" entries are honestly flagged as forward work ([21-world-class-additions.md](21-world-class-additions.md) §B9, §C).

| ID | Threat | Lab(s) |
|---|---|---|
| T1 | Memory Poisoning | L15 |
| T2 | Tool Misuse | L11, L16 |
| T3 | Privilege Compromise | L16 |
| T4 | Resource Overload | L19 |
| T5 | Cascading Hallucination | L14 |
| T6 | Intent Breaking & Goal Manipulation | L14 |
| T7 | Misaligned & Deceptive Behaviors | roadmap (B9/C) |
| T8 | Repudiation & Untraceability | L20 (logging/non-repudiation) |
| T9 | Identity Spoofing & Impersonation | L12; deeper in roadmap (B9) |
| T10 | Overwhelming Human-in-the-Loop | L16 |
| T11 | Unexpected RCE & Code Attacks | L13 |
| T12 | Agent Communication Poisoning | L14, L15; roadmap (B9) |
| T13 | Rogue Agents in Multi-Agent Systems | L14; roadmap (B9) |
| T14 | Human Attacks on Multi-Agent Systems | roadmap (C) |
| T15 | Human Manipulation | roadmap (C) |

Core agentic threats (T1–T6, T8, T10, T11) have direct labs; T7/T9/T12–T15 are partially covered or tracked as forward research — stated plainly rather than claimed as complete.

## 4. Per-item crosswalk object

Every lesson, lab, question, and finding carries a crosswalk with explicit `mapping_confidence`:

```yaml
framework_crosswalk:
  owasp:        { id: "LLM01:2025", name: "Prompt Injection", mapping_confidence: "high" }
  atlas:        { tactic_id: "AML.TA0002", technique_id: "AML.T0051.001", mapping_confidence: "medium" }
  nist_ai_rmf:  { functions: ["MAP","MEASURE","MANAGE"], risk_category: "Information Integrity", mapping_confidence: "medium" }
  agentic_ai:   { id: "tool-misuse", name: "Tool Misuse", mapping_confidence: "high" }
```

## 5. CI checks

```yaml
framework_ci:
  reject_if:
    - "OWASP id not in active framework ledger"
    - "ATLAS technique has no source version"
    - "NIST mapping missing for Track 6 / reporting lessons"
    - "mapping_confidence absent"
    - "deprecated framework id used without migration note"
```

This is the same registry the taxonomy-tag CI check validates against ([12-content-authoring.md](12-content-authoring.md)) and that the reused `detector_catalog()` ids must agree with ([09b-reuse-map.md](09b-reuse-map.md)). Monthly re-checks are owned by [20-instructor-ops-runbook.md](20-instructor-ops-runbook.md).

## Cross-references
[09a-source-library.md](09a-source-library.md) · [09b-reuse-map.md](09b-reuse-map.md) · [12-content-authoring.md](12-content-authoring.md) · [20-instructor-ops-runbook.md](20-instructor-ops-runbook.md)

## Sources
OWASP LLM Top 10: <https://genai.owasp.org/llm-top-10/> · OWASP Agentic: <https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/> · MITRE ATLAS: <https://atlas.mitre.org/> · NIST AI RMF: <https://www.nist.gov/itl/ai-risk-management-framework> · NIST AI 600-1: <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence>
