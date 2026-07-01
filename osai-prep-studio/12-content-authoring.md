# Content Authoring Standard

> Purpose: Keep ~20 labs, ~250 lessons, and ~750 gold-set questions from drifting by fixing one set of schemas and one CI check that binds everything to the shared taxonomy. This is the contract every content author and every generator follows.

## 1. The binding rule

Every lesson, lab, and question references skill-tags drawn **only** from `detector_catalog()` (`../projects/llm-log-triage/src/detectors.py`) or the framework ledger ([15-framework-version-ledger.md](15-framework-version-ledger.md)). CI rejects any unknown id. This is the mechanical enforcement of the architectural invariant ([09b-reuse-map.md](09b-reuse-map.md)).

## 2. Lesson frontmatter schema (MDX)

```yaml
lesson:
  id: "T3-L03"
  title: "Indirect Prompt Injection in RAG Systems"
  track: 3
  ai300_module: "M5"            # confidence per 00b ledger
  readiness_gate: "R3"
  claim_dependencies: ["OSAI-CLAIM-003"]   # any exam claim it relies on
  frameworks: ["LLM01:2025", "LLM08:2025"]
  authority_requirements: ["A1", "A3"]      # tutor source tiers
  labs: ["L02"]
  questions: ["Q-T3-L03-001"]
  report_skills: ["impact", "root_cause", "retest"]
  est_minutes: 45
```

## 3. Lab manifest schema

```yaml
lab:
  id: "L02"
  title: "Indirect Prompt Injection Through RAG"
  ai300_module: "M5"
  readiness_gate: "R3"
  difficulty: "medium"
  defense_variants: ["D0", "D4", "D7"]   # >=3 from the D0-D8 scale; [17-defense-bypass-ladder.md]
  authorized_scope: ["local docker network", "seeded fake corpus", "lab callback server"]
  frameworks: { owasp: ["LLM01:2025", "LLM08:2025"], atlas: ["AML.T0051.001"] }
  reuse_asset: "indirect_prompt_injection"
  complements: "PortSwigger indirect injection"
  attack_graph: "attack-graphs/L02.yml"   # [16-attack-path-graphs.md]
  two_signal_grading:
    detector_required: "indirect_prompt_injection"
    evidence_tokens:
      - { type: "flag", path: "/flags/l02.txt" }
      - { type: "audit_log", path: "/logs/policy_decisions.jsonl" }
  hint_ladder: ["direction", "methodology", "technique", "walkthrough"]
  report_required: true
  ai_modes_allowed: ["NO_AI", "SOCRATIC_AI", "AI_ASSISTED", "ATTACK_WITH_AI"]
  egress_policy: "deny_all_except_callback_container"
  cost_limit_usd: 0.50
  reset_command: "make reset-lab L=L02"
  safe_failure_mode: "lab returns to clean state on crash"
```

## 4. Question / answer-key schema

```yaml
question:
  id: "Q-T3-L03-001"
  bank: "lab_grounded"
  prompt: "..."
  mode: "Tutor"
  difficulty: "medium"
  skill_tags: ["LLM01:2025"]
  grader_type: "rubric"          # exact|keyword|rubric|judge|assert-abstain|assert-refuse|assert-flag
  expected: { rubric_points: ["names untrusted-channel boundary"] }
  sources: ["reference/owasp-llm-top-10.md#llm012025"]
  must_cite: true
  answer_key_version: "2026-06-30"   # versioned; bump on change
```

Answer keys are **versioned** (date + content hash); changing a key bumps the version and triggers gold-set regression.

## 5. CI jobs

```yaml
ci_jobs:
  validate_taxonomy_tags:        # the binding rule
    rejects: ["skill_tag/owasp_id/atlas_technique not in detector_catalog() or framework ledger"]
  validate_exam_claims:
    rejects: ["claim without status", "confirmed claim without primary source", "pending claim used as hard product behavior"]
  validate_framework_ledger:
    rejects: ["unknown OWASP/ATLAS/NIST id", "deprecated id without migration note", "missing framework version", "mapping_confidence absent"]
  validate_lab_manifests:
    rejects: ["lab without attack graph", "lab without authorized scope", "lab without evidence token", "lab without reset command", "lab missing no-AI route"]
  tutor_goldset:
    rejects: ["fabricated citation", "fabricated OffSec claim", "unsafe live-target guidance", "leaked answer key"]
  markdown_links:
    rejects: ["broken relative cross-link", "dead external URL (warn)"]
```

These extend the existing repo CI pattern (`../.github/workflows/ci.yml`, `../Makefile`, zero runtime deps).

## 6. Authoring workflow & review checklist

1. Write the lesson MDX with full frontmatter. 2. Author/extend the lab manifest + attack graph + defense variants. 3. Write ≥4 gold-set questions per new skill-tag, seeded from `../reference/owasp-llm-top-10.md`. 4. Run CI locally (`make content-check`). 5. Peer review against the checklist: taxonomy tags valid · claims labeled · authorized-lab-only · two-signal grading defined · report deliverable present · no proprietary OffSec text · citations resolve.

**Style guide:** OffSec-aligned (hands-on, honest about scope); imperative lab objectives; mark every `pending`/`inferred` exam claim inline; one finding = one OWASP id; diagrams in Mermaid.

## Cross-references
[01-curriculum.md](01-curriculum.md) · [02-lab-range.md](02-lab-range.md) · [04-evaluation-harness.md](04-evaluation-harness.md) · [09b-reuse-map.md](09b-reuse-map.md) · [15-framework-version-ledger.md](15-framework-version-ledger.md) · [16-attack-path-graphs.md](16-attack-path-graphs.md)
