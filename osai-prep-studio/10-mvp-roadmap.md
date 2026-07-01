# MVP Roadmap

> Purpose: Sequence the build **spine-first** — taxonomy, manifests, graders, tutor, report grader before any premium UX — with phase exit gates, a 30-day plan, acceptance criteria, success metrics, and a risk register. Design-only doc; building is the separately-greenlit work this sequences.

## 1. Guiding rule: build the spine before the polish

The MVP is **not** ready when the UI looks nice. It is ready when a learner can attack a lab, get two-signal-graded, ask a citation-grounded tutor, and submit a graded report. Canva, leaderboards, and SRS polish come **after** that loop works.

### Spine build order (do these in order)
1. `framework-ledger.yml` ([15-framework-version-ledger.md](15-framework-version-ledger.md)) · 2. `exam-claims.yml` ([00b-exam-blueprint.md](00b-exam-blueprint.md)) · 3. `taxonomy-registry` from `detector_catalog()` ([09b-reuse-map.md](09b-reuse-map.md)) · 4. `lab-manifest.schema` · 5. `question.schema` · 6. `finding.schema` ([12-content-authoring.md](12-content-authoring.md)) · 7. four reuse-heavy labs (L01/L04/L07/L05) · 8. two-signal **ChallengeValidator** · 9. RAG tutor with source-authority tiers · 10. report grader · 11. timed mini-exam · 12. progress/SRS · 13. Canva/Marp exports · 14. leaderboard/premium UX.

## 2. Phases & exit gates

| Phase | Days | Theme | Labs | Exit gate |
|---|---|---|---|---|
| **P1 Foundation MVP** | 1–10 | Curriculum + grader spine + first labs | L01,L04,L07,L05 | Learner reads Track 2–3 content, attacks 4 labs in-browser, auto-graded two-signal by `detectors.py` |
| **P2 Practice Range** | 11–20 | Docker range + tutor + RAG cluster | L02,L08,L09,L10,L16 | Range runs; tutor answers from corpus with citations or abstains; RAG labs grade |
| **P3 Exam Simulator** | 21–27 | Agentic/MCP/infra labs + timed engagement + report grader | L11–L15,L17–L19,L20 | Timed mini-engagement → gradable evidence bundle; report scored vs `Finding` schema |
| **P4 Premium** | 28–30+ | Gamification, SRS, Canva, gold-set hardening | — | XP/SRS live; Canva (or Marp fallback) export; gold-set passes ship gate |

## 3. Epics & acceptance criteria

**P1** — E1 content schema + 3 lessons (AC: MDX renders with skill-tag frontmatter, links a lab). E2 ChallengeValidator service (AC: POST transcript → `Finding[]`; asserts expected `owasp_id` for L01/L04/L07/L05; parity with `detector_catalog()`). E3 minimal local target (AC: 4 labs reach an Ollama model; no API key needed). E4 Next.js shell + auth + lab-runner page (AC: login → L01 → submit → see verdict + matched rationale).

**P2** — E5 Docker-Compose range + pgvector + callback (AC: `make lab-up L02`; L02/L09/L10 grade). E6 tutor retrieval pipeline (AC: every answer cites ≥1 source; abstains when none). E7 hint-ladder hooks (AC: tutor escalates hints only on repeated failure; never reveals flag).

**P3** — E8 agentic/MCP lab infra (AC: L11–L13 grade via tool-call tokens; egress blocked). E9 exam simulator (AC: subset engagement → gradable bundle). E10 report grader (AC: a known-good and known-weak report score in correct order).

**P4** — E11 progress/SRS (AC: a missed concept reschedules a card). E12 Canva + Marp fallback (AC: study pack exports; Marp works if Canva OAuth absent). E13 gold-set ≥ ship-gate ([04-evaluation-harness.md](04-evaluation-harness.md)).

## 4. The 30-day plan

- **Week 1:** source library + tutor + quiz engine (framework/claim ledgers, taxonomy registry, retrieval, gold-set v0).
- **Week 2:** AI-architecture lessons + flashcards + study exports (Track 2 content, SRS v0, Marp export).
- **Week 3:** the first three labs — prompt injection (L01), RAG leakage (L02), agent/MCP tool misuse (L11) — with two-signal grading.
- **Week 4:** timed mini-exam + report grader + progress dashboard.

## 5. MVP exit gate (definition of done)

```yaml
mvp_exit_gate:
  labs: { count: 4, two_signal_grading: true,
          must_include: ["Prompt Injection", "System Prompt Leakage or Sensitive Disclosure",
                         "Improper Output Handling", "Unbounded Consumption or Blue-Team Detection"] }
  tutor: { citations: true, abstention: true, source_authority_tiers: true }
  reporting: { finding_template: true, rubric_scoring: true }
  safety: { authorized_lab_only: true, refusal_goldset_pass: "100%" }
  ci: { framework_id_validation: true, markdown_links: true, stale_claim_tests: true }
```

## 6. Success metrics

Learner-readiness lift (R-score delta), lab pass rate after remediation, tutor abstention/refusal compliance (100% refusal), gold-set pass margin, time-to-first-finding in the mini-exam, report-quality score trend.

## 7. Risk register

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | Safe local model hosting (exploitable but not harmful; GPU/cost) | H | H | small Ollama/CPU models with deliberately weak guardrails (mirror `MockTarget`); egress deny-all; token/context caps ([21-world-class-additions.md](21-world-class-additions.md) §local-models) |
| R2 | Auto-grading reliability (regex FN/FP; gaming sentinels) | M | H | two-signal grading (detector + produced evidence token); versioned answer-keys; manual-review escape hatch |
| R3 | Tutor hallucination (confident wrong advice) | H | H | retrieval-first + citation enforcement + taxonomy-ID validation + hard gold-set ship gate ([04-evaluation-harness.md](04-evaluation-harness.md)) |
| R4 | Docker lab isolation / escape | M | C | ephemeral per-lab containers, no-new-privileges, read-only rootfs, egress allowlist, resource limits ([13-platform-threat-model.md](13-platform-threat-model.md)) |
| R5 | Tutor weaponization (jailbroken into a real attack tool) | M | H | scope-guard + refusal + lab-scoped context; `tutor_self_redteam` suite at 100% |
| R6 | Cost / denial-of-wallet on the router | M | M | local-first routing, caching, per-user spend caps; dogfood the LLM10 detector |
| R7 | Content drift (20 labs + 250 lessons + 750 Q vs one taxonomy) | M | M | taxonomy-tag CI check vs `detector_catalog()` ([12-content-authoring.md](12-content-authoring.md)) |
| R8 | Exam-spec uncertainty (module/report detail `pending`) | M | M | claim ledger + `exam_config.yml`; spec changes are one-file edits ([00b-exam-blueprint.md](00b-exam-blueprint.md)) |

## Cross-references
[02-lab-range.md](02-lab-range.md) · [03-tutor-examiner-bot.md](03-tutor-examiner-bot.md) · [04-evaluation-harness.md](04-evaluation-harness.md) · [12-content-authoring.md](12-content-authoring.md) · [13-platform-threat-model.md](13-platform-threat-model.md)
