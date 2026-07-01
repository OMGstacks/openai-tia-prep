# Readiness Operating System

> Purpose: Make "Am I ready?" a question the product answers continuously, not one the learner guesses at. Defines readiness gates R0–R5, a scored readiness model, a diagnostic, and a personal remediation generator. Integrates the uploaded world-class addendum.

## 1. Readiness gates

| Gate | Name | Goal | Passing evidence |
|---|---|---|---|
| `R0` | Operator Setup | Work like an OffSec learner | Kali/Linux comfort, Docker, Git, Python, HTTP/API basics, Burp-style workflow, notes/report template |
| `R1` | Cybersecurity Foundation | Reason through app/infra issues AI inherits | Recon, web/API testing, authz/authn, secrets, logging, Linux/Windows basics, cloud IAM basics |
| `R2` | AI Systems Understanding | Diagram and explain the AI target | Maps prompts, system prompts, RAG, embeddings, vector DB, tools, agents, MCP, gateway, logs, cloud |
| `R3` | AI Red Team Execution | Find/exploit AI-layer vulns in authorized labs | Passes LLM/RAG/agentic/supply-chain/infra labs with two-signal evidence + valid report snippets |
| `R4` | Exam Operator | Complete a timed engagement + coherent report | Timed mini-exam, evidence bundle, exec summary, findings, remediation, retest |
| `R5` | Professional AI Red Teamer | Transfer skills to real work ethically | Business-impact findings, OWASP/ATLAS/NIST mapping, control proposals, no unauthorized behavior |

Gates map to tracks ([01-curriculum.md](01-curriculum.md)): R0→T0, R1→T1, R2→T2, R3→T3–T5, R4→exam mode, R5→T6/reporting.

## 2. Readiness score

```yaml
readiness_score:
  total_points: 1000
  gates:
    R0_operator_setup: 100
    R1_cyber_foundation: 150
    R2_ai_systems: 150
    R3_ai_exploitation: 250
    R4_exam_operator: 250
    R5_professional_translation: 100
  minimum_exam_ready:
    total_score: 780
    mandatory:
      - "R0 >= 80%"
      - "R2 >= 75%"
      - "R3 >= 75%"
      - "R4 >= 80%"
      - "No critical weakness in reporting"
      - "No failed refusal-policy test"
```

The readiness score — not XP — is the headline metric a learner sees ([05-progress-engine.md](05-progress-engine.md)). The studio recommends booking the exam only after the exam-ready threshold is met.

## 3. Diagnostic exam

A placement test run before the learner starts, producing per-gate remediation:

| Section | Items | Output |
|---|---:|---|
| Linux / shell / files | 20 | R0 plan |
| Networking / HTTP / APIs | 25 | R1 plan |
| Web / appsec | 25 | R1 plan |
| Python / scripting | 15 | R0/R1 plan |
| AI systems concepts | 25 | R2 plan |
| OWASP GenAI Top 10 | 20 | R2/R3 plan |
| RAG / embedding / agent reasoning | 25 | R2/R3 plan |
| Reporting judgment | 10 | R4/R5 plan |

## 4. Personal remediation generator

Every failed diagnostic (or lab) item emits a remediation item routed by skill-tag:

```yaml
remediation_item:
  skill_tag: "LLM01:2025"
  failed_evidence: "Could not distinguish direct vs indirect prompt injection."
  recommended_lesson: "T3-L08 (indirect injection)"
  recommended_lab: "L02"
  flashcards_added: 8
  recheck_after: "2 successful lab attempts or 48 hours"
```

These feed the SRS and weakness heatmap ([05-progress-engine.md](05-progress-engine.md)) and the retake plan ([06-exam-simulator.md](06-exam-simulator.md)), closing the adaptive loop.

## Cross-references
[00b-exam-blueprint.md](00b-exam-blueprint.md) · [01-curriculum.md](01-curriculum.md) · [05-progress-engine.md](05-progress-engine.md) · [06-exam-simulator.md](06-exam-simulator.md)
