# OSAI Prep Studio — Blueprint Suite

> An OffSec-style **interactive training range** for AI red teaming. North star: make a learner able to **pass the OffSec AI-300 / OSAI exam and excel in the role** — hands-on labs, scenario questions, reporting practice, a citation-grounded tutor/examiner bot, and a progress engine that *proves* improvement.

**This is a design-only blueprint** (schemas, specs, rubrics, file trees, acceptance criteria — no app code yet). It is built **reuse-first** on the existing [`llm-threat-triage`](../README.md) detection engine, framework references, and red-team harness. Scope and decisions were confirmed with the project owner: blueprint suite only, in this repo.

> Exam facts are **confidence-labeled** (`confirmed` / `inferred` / `pending` / `deprecated`) per the claim ledger in [00b-exam-blueprint.md](00b-exam-blueprint.md). AI-300/OSAI is new (2026) and some exam details are still being finalized by OffSec.

## Executive summary

OSAI Prep Studio turns passive AI-security study into reps in an authorized range. Its coherence comes from **one taxonomy spine** — the `owasp_id` / `atlas_technique` / `detector` / `severity` fields from the existing detection engine are simultaneously the grader verdict, lesson skill-tag, spaced-repetition unit, gold-set label, and report finding-classifier. Labs are **two-signal graded** (reused detector verdict **and** a produced evidence token), scored on **attack-path graphs** (methodology, not flag-hunting), and shipped across **defense-maturity variants** (D0–D8). The **tutor** is retrieval-first, citation-enforced, abstaining, and gated behind a hard evaluation harness. Reporting is a **first-class, rubric-graded deliverable** (a required exam deliverable most prep ignores; its exact weight is unpublished, so we over-invest deliberately). A claim ledger and a framework-version ledger keep the whole thing **drift-resistant**.

## Document map

| # | Doc | What it covers |
|---|-----|----------------|
| — | [00a-vision.md](00a-vision.md) | Product vision, six pillars, personas, differentiators |
| — | [00b-exam-blueprint.md](00b-exam-blueprint.md) | **Normative** cited exam spec + claim-confidence ledger + exam-day playbook |
| 01 | [01-curriculum.md](01-curriculum.md) | Tracks 0–6 reconciled to AI-300's 11 modules |
| 02 | [02-lab-range.md](02-lab-range.md) | Dockerized range architecture + the **20-lab catalog** |
| 03 | [03-tutor-examiner-bot.md](03-tutor-examiner-bot.md) | Retrieval-first tutor; 7 modes; anti-hallucination; refusal |
| 04 | [04-evaluation-harness.md](04-evaluation-harness.md) | Gold set (~750 Q), RAG metrics, **ship gate**, tutor self-red-team |
| 05 | [05-progress-engine.md](05-progress-engine.md) | Mastery/skill-graph, FSRS, weakness heatmap, XP/leaderboard |
| 06 | [06-exam-simulator.md](06-exam-simulator.md) | Timed multi-target engagement, scoring, retake plan |
| 07 | [07-architecture-and-stack.md](07-architecture-and-stack.md) | Stack, system diagram, data model, API surface |
| 08 | [08-reporting-and-canva.md](08-reporting-and-canva.md) | Report templates, **Report-Reviewer**, Canva/Marp study packs |
| 09a | [09a-source-library.md](09a-source-library.md) | The tutor's cited RAG corpus (authority-tiered) |
| 09b | [09b-reuse-map.md](09b-reuse-map.md) | Existing repo asset → studio component; the **invariant** |
| 10 | [10-mvp-roadmap.md](10-mvp-roadmap.md) | Spine-first build order, 30-day plan, **risk register** |
| 11 | [11-safety-legal-ethics.md](11-safety-legal-ethics.md) | Authorized-lab-only, refusal policy, IP boundary |
| 12 | [12-content-authoring.md](12-content-authoring.md) | Lesson/lab/question schemas + taxonomy CI |
| 13 | [13-platform-threat-model.md](13-platform-threat-model.md) | The platform's own threat model (isolation, egress) |
| 14 | [14-readiness-model.md](14-readiness-model.md) | Readiness gates R0–R5, diagnostic, remediation |
| 15 | [15-framework-version-ledger.md](15-framework-version-ledger.md) | Versioned OWASP/ATLAS/NIST mappings, anti-drift |
| 16 | [16-attack-path-graphs.md](16-attack-path-graphs.md) | Methodology scoring graphs |
| 17 | [17-defense-bypass-ladder.md](17-defense-bypass-ladder.md) | D0–D8 defense-maturity variants |
| 18 | [18-ai-use-policy-for-exam-mode.md](18-ai-use-policy-for-exam-mode.md) | AI-allowed exam posture; practice modes |
| 19 | [19-business-impact-rubric.md](19-business-impact-rubric.md) | Finding template, severity model, report scoring |
| 20 | [20-instructor-ops-runbook.md](20-instructor-ops-runbook.md) | Monthly update ritual, broken-lab IR |
| 21 | [21-world-class-additions.md](21-world-class-additions.md) | Addendum integration + original R&D layer |

## Traceability matrix — AI-300 modules → tracks → docs → labs → frameworks

| AI-300 module (titles `inferred`) | Track | Primary docs | Labs | OWASP / ATLAS / agentic |
|---|---|---|---|---|
| M1 Intro to RT'ing AI | T2 | 00a, 01, 09a | — | LLM01–10 + ATLAS + NVIDIA Kill Chain |
| M2 Recon for AI targets | T3 | 01, 02 | L08 | recon `AML.TA0002`, LLM08 |
| M3 Single-agent / LLM-app | T3 | 02, 03 | L01,L03,L04,L05,L06,L07 | LLM01/02/05/07; `T0051/54/56/57/24` |
| M4 Multi-agent | T4 | 02 | L14,L15,L16 | agentic; `T0053`, persistence |
| M5 RAG-pipeline | T3 | 02 | L02,L08,L09,L10 | LLM01/04/08; `T0051.001` |
| M6 MCP tool-surface | T4 | 02 | L11,L12,L13 | agentic tool misuse/shadowing/RCE |
| M7 Supply-chain | T4 | 02 | L17 | LLM03 |
| M8 Cloud ML services | T5 | 02 | L18 | LLM10/03 |
| M9 K8s / model-server / adversarial ML | T5 | 02 | L18,L19 | LLM10, extraction/evasion |
| M10 Synthesis / threat modeling | T6 | 08,19,20 | L20 | all (defensive) |
| M11 Capstone (MegacorpAI) | T6 | 06,21 | L20 + engagement | all |

OWASP coverage check: **LLM01** L01/L02/L03 · **LLM02** L07 · **LLM03** L17 (+ infra L18/L19) · **LLM04** L09 · **LLM05** L05/L06 (+ L13 RCE sink) · **LLM06** L16 · **LLM07** L04 · **LLM08** L08/L10 · **LLM09** L14 + tutor anti-hallucination · **LLM10** L18/L19. Named OWASP Agentic threats (T1–T15) are mapped in [15-framework-version-ledger.md](15-framework-version-ledger.md) §3.1. Every module and every OWASP category is covered.

## Hardening-layer traceability (from the world-class addendum)

| Addition | File | Why it matters |
|---|---|---|
| Claim confidence ledger | [00b-exam-blueprint.md](00b-exam-blueprint.md) | Prevents stale/inferred OffSec details from becoming product truth |
| Readiness operating system | [14-readiness-model.md](14-readiness-model.md) | Converts the course into measurable readiness gates |
| Framework version ledger | [15-framework-version-ledger.md](15-framework-version-ledger.md) | Prevents OWASP/ATLAS/NIST drift |
| Attack-path graphs | [16-attack-path-graphs.md](16-attack-path-graphs.md) | Scores methodology, not just flags |
| Defense bypass ladder | [17-defense-bypass-ladder.md](17-defense-bypass-ladder.md) | Trains against increasingly mature defenses |
| AI-use exam-mode policy | [18-ai-use-policy-for-exam-mode.md](18-ai-use-policy-for-exam-mode.md) | Handles OffSec's AI-allowed OSAI posture without dependency or drift |
| Business-impact rubric | [19-business-impact-rubric.md](19-business-impact-rubric.md) | Turns exploitation into professional reporting |

## How it reuses `llm-threat-triage`

~65% of the detection/grading logic is reusable on day zero — the 9 detectors become the exploit auto-grader and report classifier, the SQL analyses become blue-team labs, the references seed the RAG corpus, and the red-team harness becomes the attack library. Full mapping in [09b-reuse-map.md](09b-reuse-map.md).

## Status

Design-only blueprint, complete — **25 files** (this README + 24 blueprint docs). Building the platform is a **separately greenlit** phase, sequenced spine-first in [10-mvp-roadmap.md](10-mvp-roadmap.md). Authorized-lab-only; no proprietary OffSec content; all external claims cited and confidence-labeled.

## Sources
OffSec AI-300: <https://www.offsec.com/courses/ai-300/> · OSAI Exam FAQ: <https://help.offsec.com/hc/en-us/articles/46669767163156-OSAI-Advanced-AI-Red-Teaming-Exam-FAQ> · OWASP LLM Top 10 (2025): <https://genai.owasp.org/llm-top-10/> · OWASP Agentic Threats: <https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/> · MITRE ATLAS: <https://atlas.mitre.org/> · NIST AI RMF / 600-1: <https://www.nist.gov/itl/ai-risk-management-framework>
