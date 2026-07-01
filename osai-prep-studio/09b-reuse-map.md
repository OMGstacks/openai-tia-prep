# Reuse Map — existing repo → OSAI Prep Studio

> Purpose: The engineering map from the existing `llm-threat-triage` assets to OSAI Prep Studio components, and the statement of the **shared-taxonomy invariant** that holds the product together. ~65% of the detection/grading logic is reusable on day zero.

## 1. The architectural invariant

> The `Finding` fields **`owasp_id` + `atlas_technique` + `detector` + `severity`** (defined in `../projects/llm-log-triage/src/detectors.py`, enumerated by `detector_catalog()`) are **one taxonomy serving five consumers at once**: the grader **verdict**, the lesson **skill-tag**, the spaced-repetition **mastery unit**, the gold-set **label**, and the report **finding-classifier**.

A CI check validates that every lab manifest, lesson frontmatter, and gold-set question references only ids present in `detector_catalog()` or the framework ledger ([15-framework-version-ledger.md](15-framework-version-ledger.md)). This single invariant is why the six pillars cohere instead of drifting into disconnected tools.

## 2. Asset → component table

| Repo asset | What it is | Studio component | Reuse level | Concrete reuse idea |
|---|---|---|---|---|
| `src/detectors.py` (`ALL_DETECTORS`, `Finding`, `detector_catalog()`) | 9 OWASP/ATLAS-mapped detectors + helpers (evasion-resistant matching, base64/hex decode, Luhn, entropy, severity rollup) | **ChallengeValidator** auto-grader (Signal A) + report finding-classifier + lab answer-keys + the taxonomy spine | **As-is** (wrap behind a service) | POST a learner transcript → `Finding[]`; assert the lab's expected `owasp_id`/`severity` |
| `src/normalize.py` | messy-log → canonical event schema (field aliases, role/source mapping, timestamp parsing, content extraction) | Lab-log ingestion → grader input | **Adapt** (add `attack_type`) | Normalize lab transcripts so detectors score them consistently |
| `src/pipeline.py` | load → normalize → detect → summarize → report | Learner-evaluation flow + report card | **As-is** | `format_report()` extended for learner-facing feedback |
| `src/generate_logs.py` | seeded messy synthetic logs, ~18% adversarial across 9 classes | Lab traffic / scenario generator + difficulty slider | **Adapt** | Parameterize by attack mix + difficulty for L20 and exam scenarios |
| `sql/schema.sql` + `v_triage` | events/detections schema + analyst view | Platform data model seed | **Adapt** | Add `learner_id`, `cohort_id`, `lab_id`, progress tables |
| `sql/analysis/01..07` | 7 analyst queries incl. `06` consumption-anomaly (LLM10) and `07` session-escalation (multi-turn) | Blue-team/detection labs (**L20**) + exam analytics + L19 detection side | **As-is** | Each query is a triage challenge; `07` is the capstone escalation finding |
| `red-team/local_redteam_harness.py` | offline attack→target→grader loop; `MockTarget` ("blocks the obvious, leaks on the subtle") | Offline **attack library** + first **Defense Lab** (D0/D1 target template) | **As-is** | Learners tune the guardrail to block more payloads → points |
| `red-team/pyrit/prompt_injection_probe.py` | PyRIT-style probe + scorer, std-lib mock | Attack-with-AI starter + payload bank | **As-is / inspiration** | Seeds the `ATTACK_WITH_AI` mode and L01/L11 automation extensions |
| `red-team/garak/`, `red-team/promptfoo/` | scanner + eval configs | Advanced-lab integrations + eval harness presets | **Adapt** | promptfoo config seeds [04-evaluation-harness.md](04-evaluation-harness.md) |
| `reference/owasp-llm-top-10.md` | exhaustive per-category what/attack/detect(regex+SQL)/mitigate; names the **non-log-detectable** categories | Curriculum spine + **RAG source library** seed + gold-set seeds + the build-vs-reuse boundary | **As-is** | Tutor cites it; its "not detectable from logs" section is the lab build/buy boundary (§4) |
| `reference/mitre-atlas.md` | ATLAS technique reference + detector crosswalk | Threat-modeling lessons + exam rubric refs | **As-is** | Each lab names its `AML.Txxxx`; reports must cite it |
| `reference/glossary.md` | ~30 adversarial-ML/LLM terms | Tutor KB + learner reference | **As-is** | Tutor answers "what is a jailbreak?" from it |
| `docs/playbook/analyst-runbook.md` | triage loop, per-class SOPs, severity rubric, escalation | Report-Reviewer **rubric** + Track 6 "professional playbook" | **As-is** | Basis of [19-business-impact-rubric.md](19-business-impact-rubric.md) |
| `docs/llm-log-triage-case-study.pdf` | one-page case study | Report exemplar | **As-is** | Gold standard for the report grader |
| `Makefile`, `.github/workflows/ci.yml` | demo/test/queries targets; 3.10–3.12 CI; zero runtime deps | Eval-harness CI pattern + lab build pattern | **Pattern** | `make`-driven gold-set + framework-ledger CI |
| `tests/` (550 lines) | unit tests per detector + hardening + pipeline | Auto-grader test harness | **As-is + extend** | Each test → a learner challenge; add adversarial cases |

## 3. The build-vs-reuse boundary

`../reference/owasp-llm-top-10.md` explicitly enumerates which OWASP categories are **not** detectable from inference logs and why. That is precisely the line between "reuse the regex grader" and "build new lab infra":

| Detect from logs (reuse `detectors.py`) | Needs new lab infra (build) |
|---|---|
| LLM01 (L01–L03), LLM02 (L07), LLM05 (L05/L06), LLM06 (L16), LLM07 (L04), LLM10 detection (`06`) | LLM03 supply-chain artifacts (L17), LLM04 poisoning write-path (L09), LLM08 retrieval-layer (L08/L10), LLM09 correctness (woven into L14 + tutor anti-hallucination), cloud/model-server (L18/L19) |

## 4. Gap list — what must be built (and who owns it)

| Gap | Owner doc |
|---|---|
| Web UI / dashboard, auth, multi-tenancy | [07-architecture-and-stack.md](07-architecture-and-stack.md) |
| Gamification + spaced-repetition engine | [05-progress-engine.md](05-progress-engine.md) |
| Dockerized vulnerable-AI lab images + isolation | [02-lab-range.md](02-lab-range.md), [13-platform-threat-model.md](13-platform-threat-model.md) |
| Agentic/multi-agent + MCP + RAG-leak + cloud lab infra | [02-lab-range.md](02-lab-range.md) |
| Citation-grounded tutor (RAG + judge) | [03-tutor-examiner-bot.md](03-tutor-examiner-bot.md) |
| Report grader/rubric | [08-reporting-and-canva.md](08-reporting-and-canva.md), [19-business-impact-rubric.md](19-business-impact-rubric.md) |
| Exam simulator (timed, multi-target, scoring) | [06-exam-simulator.md](06-exam-simulator.md) |
| Readiness model + diagnostic | [14-readiness-model.md](14-readiness-model.md) |
| Framework/claim version governance + CI | [15-framework-version-ledger.md](15-framework-version-ledger.md), [00b-exam-blueprint.md](00b-exam-blueprint.md) |

## Cross-references
[09a-source-library.md](09a-source-library.md) · [02-lab-range.md](02-lab-range.md) · [04-evaluation-harness.md](04-evaluation-harness.md) · [07-architecture-and-stack.md](07-architecture-and-stack.md)
