# Curriculum — Tracks 0–6, reconciled to AI-300

> Purpose: The full learning path. It reconciles the studio's seven pedagogical tracks with AI-300's eleven exam modules, tags every Track-3+ lesson to a module and a framework id, and points each lesson at the lab that proves it. Exam specifics are confidence-labeled per [00b-exam-blueprint.md](00b-exam-blueprint.md).

## 1. The reconciliation rule

The studio's **tracks** are a *pedagogical ramp* (including the prereqs AI-300 only *recommends*); AI-300's **11 modules** are the *exam scope*. They are not in conflict:

> **Tracks 0–2 are pre-AI-300 scaffolding** (the recommended fundamentals + OffSec's LLM Red Teaming prereq path). **Tracks 3–6 are the AI-300 body**, and **every Track-3+ lesson carries an `ai300_module` tag** plus a framework crosswalk ([15-framework-version-ledger.md](15-framework-version-ledger.md)) and a `readiness_gate` ([14-readiness-model.md](14-readiness-model.md)).

| Track | Studio scope | AI-300 module(s) | Readiness gate | Primary OWASP / Agentic + ATLAS | NIST AI RMF | Exam domain |
|---|---|---|---|---|---|---|
| **0 Setup** | Env, Docker, Ollama/Open WebUI, tooling (PyRIT/garak/promptfoo), notes/report template | (pre) | R0 | — | Govern | Engagement setup |
| **1 Pentest Foundation** | Linux/Win, networking, web (Burp), APIs, scripting, recon mindset, evidence capture | (assumed prereq) | R1 | Recon `AML.TA0002` | — | Recon, methodology |
| **2 AI Systems Fundamentals** | How LLM apps/RAG/embeddings/agents/MCP/gateways/cloud-AI are built; trust boundaries; the four frameworks | M1 | R2 | LLM01–10 orientation | Map | Framework fluency |
| **3 LLM / RAG Red Team** | Prompt injection, jailbreak, sys-prompt leak, output handling; RAG recon/poisoning/vector weaknesses | M2, M3, M5 | R3 | LLM01,02,05,07,08,09,04; `T0051.0/.1`, `T0054`, `T0056`, `T0057`, `T0024` | Measure | AI-layer (RAG) exploit |
| **4 Agentic Red Team** | Multi-agent, MCP tool-surface, excessive agency, memory poisoning, tool shadowing/rug-pull, supply chain | M4, M6, M7 | R3 | LLM03,06 + agentic threats; `T0053`, persistence | Measure/Manage | AI-layer (agentic) exploit |
| **5 AI Infra / Cloud** | Cloud ML services, K8s, model-server (Triton/vLLM) exploitation, adversarial ML, model extraction | M8, M9 | R3 | LLM10,03; extraction, evasion | Manage | Infra-layer exploit, post-exploit |
| **6 Defense / Detection / Reporting** | Blue-team detection (reuse detectors+SQL), guardrail design, professional reporting, capstone | M10, M11 | R4–R5 | all (defensive view) | Manage | Reporting + capstone |

## 2. Three decisions baked into the curriculum

1. **Reporting gets outsized investment.** OffSec requires a professional report; whether it is weighted equally with findings is `pending` (OSAI-CLAIM-011), but it is the field's most under-built skill and a clear differentiator. Track 6 + [08-reporting-and-canva.md](08-reporting-and-canva.md) + [19-business-impact-rubric.md](19-business-impact-rubric.md) treat it as a graded, first-class deliverable.
2. **MCP and RAG are first-class.** AI-300 dedicates modules to each (M5, M6) and the best public labs target them. Tracks 3 and 4 carry **≥4 labs each** here.
3. **Every Track 3–5 lab ends with "automate it with AI."** A PyRIT/garak/attacker-LLM extension on each offensive lab, per the AI-allowed exam rule ([18-ai-use-policy-for-exam-mode.md](18-ai-use-policy-for-exam-mode.md)).

## 3. The taxonomy & grading invariant (why lessons and labs line up)

Every lesson, lab, question, and report finding shares ONE taxonomy — the `owasp_id` / `atlas_technique` / `detector` / `severity` fields from `../projects/llm-log-triage/src/detectors.py` (`detector_catalog()`). That single set of tags is the lesson **skill-tag**, the lab **answer-key**, the gold-set **label**, the SRS **mastery unit**, and the report **finding-classifier** (see [09b-reuse-map.md](09b-reuse-map.md)). Labs are graded **two-signal**: the reused detector verdict *and* a produced evidence token. A lesson is "mastered" only when its labs pass and its spaced-repetition cards are retained.

## 4. Tracks in detail

Each lesson below lists **objective · lab(s) · deliverable · assessment · mapping**. Lab ids refer to the catalog in [02-lab-range.md](02-lab-range.md).

### Track 0 — Setup (Foundation Academy) · gate R0
- **0.1 The operator environment** — *obj:* stand up Kali/Ubuntu, Docker, Git, Python, an HTTP/API workflow (Burp/curl). *deliverable:* a working box + notes vault + report template. *assess:* R0 diagnostic (Linux/shell/Docker/Git/Python).
- **0.2 The local AI lab** — *obj:* run Ollama + Open WebUI; pull a small instruct model; hit it via API. *lab:* range bootstrap. *deliverable:* a model you can prompt locally. *assess:* successful local completion + API call.
- **0.3 Red-team tooling tour** — *obj:* install/run PyRIT, garak, promptfoo offline against a mock target (reuse `../red-team/local_redteam_harness.py`). *deliverable:* one offline attack run. *assess:* harness coverage table produced.

### Track 1 — Pentest Foundation · gate R1
- **1.1 Enumeration methodology**, **1.2 Web & API testing** (authz/authn, IDOR, SSRF, file upload, path traversal), **1.3 Secrets & logging**, **1.4 Cloud IAM & storage basics**, **1.5 Linux/Windows privilege concepts**, **1.6 Evidence capture & note discipline.** Each: *obj* concept fluency applied to AI-adjacent infra; *deliverable* a short writeup; *assess* R1 diagnostic + a mini web/API challenge. *mapping:* recon `AML.TA0002`. These exist because AI systems inherit ordinary app/infra weaknesses — the non-prompt attack surface.

### Track 2 — AI Systems Fundamentals (AI Security Core) · gate R2 · AI-300 M1
- **2.1 Anatomy of an LLM app** — system/developer/user prompts, context windows, tokens, model APIs, gateways.
- **2.2 RAG & embeddings** — chunking, embeddings, vector DBs, retrieval, the retrieval trust boundary.
- **2.3 Agents, tools & MCP** — function calling, tool schemas, the Model Context Protocol surface, memory/session state.
- **2.4 The four frameworks** — OWASP LLM Top 10 (2025), OWASP Agentic Threats, MITRE ATLAS, **NVIDIA AI Kill Chain** (see [21-world-class-additions.md](21-world-class-additions.md) §kill-chain). *deliverable:* a trust-boundary diagram of a sample AI app. *assess:* R2 diagnostic (architecture reasoning + OWASP recall). *mapping:* LLM01–10 orientation. *reuse:* `../reference/owasp-llm-top-10.md`, `../reference/mitre-atlas.md`, `../reference/glossary.md`.

### Track 3 — LLM / RAG Red Team · gate R3 · M2, M3, M5
- **3.1 Recon & fingerprinting** — enumerate endpoints, model/version, safety mechanisms, RAG behavior. *lab:* **L08**. *map:* `AML.TA0002`, LLM08.
- **3.2 Direct prompt injection & guardrail bypass.** *lab:* **L01**. *map:* LLM01/`T0051.000`.
- **3.3 Jailbreaks & persona override.** *lab:* L01 (jailbreak variant). *map:* LLM01/`T0054`.
- **3.4 Encoded/obfuscated payloads & evasion.** *lab:* **L03**. *map:* LLM01/`T0051.001`.
- **3.5 System-prompt extraction.** *lab:* **L04**. *map:* LLM07/`T0056`.
- **3.6 Sensitive information disclosure.** *lab:* **L07**. *map:* LLM02/`T0057`.
- **3.7 Improper output handling — exfil & sinks.** *labs:* **L05, L06**. *map:* LLM05/`T0024`.
- **3.8 Indirect injection via RAG.** *lab:* **L02**. *map:* LLM01/`T0051.001`.
- **3.9 RAG poisoning & vector weaknesses.** *labs:* **L09, L10**. *map:* LLM04, LLM08.
- *deliverable per lab:* a finding writeup; *assess:* two-signal pass + report snippet graded by [19-business-impact-rubric.md](19-business-impact-rubric.md). *AI extension:* automate each with PyRIT/garak.

### Track 4 — Agentic Red Team · gate R3 · M4, M6, M7
- **4.1 MCP tool poisoning** (**L11**), **4.2 tool shadowing & rug-pull** (**L12**), **4.3 MCP→RCE** (**L13**), **4.4 multi-agent goal/intent manipulation** (**L14**), **4.5 agent memory poisoning** (**L15**), **4.6 excessive agency → destructive action** (**L16**), **4.7 supply-chain: poisoned model/adapter** (**L17**). *map:* agentic threats + LLM03/06; `T0053`, persistence. *complements:* Damn Vulnerable MCP, AI Goat. *AI extension:* drive multi-step agent attacks with an attacker-LLM.

### Track 5 — AI Infra / Cloud · gate R3 · M8, M9
- **5.1 Cloud ML service & model-server exploitation** (**L18**) — misconfigured Triton/vLLM endpoints, SSRF to internal model APIs, cloud IAM.
- **5.2 Adversarial ML & model extraction** (**L19**) — systematic query campaigns; denial-of-wallet; pair with the consumption-anomaly detector. *map:* LLM10, LLM03, extraction/evasion.

### Track 6 — Defense, Detection & Reporting · gates R4–R5 · M10, M11
- **6.1 Blue-team detection & triage** (**L20**) — run the full reused detector suite + the 7 SQL analyses over a mixed log; produce OWASP-tagged triage incl. the session-escalation finding. *reuse:* `../projects/llm-log-triage/` end-to-end.
- **6.2 Build-your-own-detector** — write a detector, measure precision/recall vs a labeled corpus (purple-team loop; see [21-world-class-additions.md](21-world-class-additions.md)).
- **6.3 Professional reporting** — finding template, business impact, executive summary, technical appendix, retest. *reuse:* `../docs/playbook/analyst-runbook.md`, `../docs/llm-log-triage-case-study.pdf`.
- **6.4 Capstone: MegacorpAI engagement** (**L20** + composed engagement, [06-exam-simulator.md](06-exam-simulator.md)) — a timed multi-target run ending in a full report. *assess:* R4–R5 gates.

## 5. Lab coverage map (full catalog in [02-lab-range.md](02-lab-range.md))

- **LLM01** L01/L02/L03 · **LLM02** L07 · **LLM03** L17 (+ infra L18/L19) · **LLM04** L09 · **LLM05** L05/L06 (+ L13 RCE sink) · **LLM06** L16 · **LLM07** L04 · **LLM08** L08/L10 · **LLM09** woven into L14 + tutor anti-hallucination · **LLM10** L18/L19.
- **Named OWASP Agentic threats (T1–T15):** mapped lab-by-lab in [15-framework-version-ledger.md](15-framework-version-ledger.md) §3.1 (core threats have direct labs; a few are forward-roadmap, flagged honestly).
- **Agentic** (memory poisoning L15, tool misuse L11, privilege compromise L16, cascading hallucination/goal manipulation L14, tool shadowing + rug-pull L12, malicious code exec L13) · **MCP** L11–L13 · **RAG** L02/L08/L09/L10 · **cloud/infra** L18/L19 · **supply chain** L17 · **blue-team capstone** L20.
- **Module coverage:** M1→T2; M2,M3,M5→T3; M4,M6,M7→T4; M8,M9→T5; M10,M11→T6.

## Cross-references
[00b-exam-blueprint.md](00b-exam-blueprint.md) · [02-lab-range.md](02-lab-range.md) · [14-readiness-model.md](14-readiness-model.md) · [15-framework-version-ledger.md](15-framework-version-ledger.md) · [16-attack-path-graphs.md](16-attack-path-graphs.md) · [19-business-impact-rubric.md](19-business-impact-rubric.md)

## Sources
- OffSec LLM Red Teaming learning path: <https://www.offsec.com/learning/paths/llm-red-teaming/>
- OWASP Top 10 for LLM Applications (2025): <https://genai.owasp.org/llm-top-10/>
- MITRE ATLAS: <https://atlas.mitre.org/>
