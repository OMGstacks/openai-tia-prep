# AI-Use Policy for Exam Mode

> Purpose: Prepare learners for the OSAI exam's **AI-allowed** posture (OSAI-CLAIM-007, guidelines `pending`) without teaching dependency or training behavior that final exam rules might later prohibit. Integrates the uploaded addendum.

## 1. Why this is mandatory

OffSec confirms AI usage *will* be allowed in the OSAI exam, with specific guidelines to be shared closer to release. That is unique among OffSec exams and cuts both ways: the studio must build the **skill of working with AI** *and* the **resilience to work without it**, while staying ready to snap to whatever final rule OffSec publishes.

## 2. Practice modes

| Mode | AI assistance | Purpose |
|---|---|---|
| `NO_AI` | Disabled except static course content | Build raw operator skill + exam resilience |
| `SOCRATIC_AI` | Questions + conceptual hints only | Reasoning without giving steps away |
| `HINT_LADDER` | Graduated hints, logged + penalized | Rescue stuck learners while preserving signal |
| `AI_ASSISTED` | AI may summarize docs, explain code, suggest tests, review report | Practice the realistic allowed-AI workflow |
| `ATTACK_WITH_AI` | PyRIT / garak / attacker-LLM — **lab targets only** | Modern AI red-team automation skill |
| `EXAM_CURRENT` | Mirrors the latest confirmed OffSec OSAI AI rule | Switchable once the final guide publishes |

Every Track 3–5 lab and the exam simulator expose a `NO_AI` and an `AI_ASSISTED`/`ATTACK_WITH_AI` route ([01-curriculum.md](01-curriculum.md), [06-exam-simulator.md](06-exam-simulator.md)).

## 3. AI-use ledger

Every AI-assisted action is logged (hashed) — for the learner's self-review and for honest exam-mode discipline:

```yaml
ai_use_event:
  timestamp: "2026-06-30T12:00:00Z"
  user_id: "local-user"
  lab_id: "L11"
  mode: "AI_ASSISTED"
  tool: "TutorBot"
  purpose: "Explain MCP tool trust boundary"
  learner_prompt_hash: "sha256:..."
  assistant_response_hash: "sha256:..."
  artifact_created: "notes/l11-tool-boundary.md"
  allowed_by_policy: true
```

## 4. Exam-mode restrictions (data-driven)

`EXAM_CURRENT` is **configuration, not code** — it reads from `exam_config.yml` ([00b-exam-blueprint.md](00b-exam-blueprint.md)) so a published rule change is a one-file edit:

```yaml
exam_ai_policy:
  source: "OffSec OSAI Exam FAQ / Exam Guide"
  last_verified: "2026-06-30"
  ai_allowed: true
  allowed_uses: ["pending-final-guidelines"]
  prohibited_uses: ["pending-final-guidelines"]
  uncertainty_banner: "OffSec says AI use will be allowed, but final usage guidelines are pending. This mode updates when the OSAI Exam Guide publishes final rules."
```

Until guidelines publish, the mode shows the uncertainty banner and treats specific allowed/prohibited uses as `pending` (never presented as official). The monthly ritual ([20-instructor-ops-runbook.md](20-instructor-ops-runbook.md)) re-checks the FAQ and updates this file.

## Cross-references
[00b-exam-blueprint.md](00b-exam-blueprint.md) · [03-tutor-examiner-bot.md](03-tutor-examiner-bot.md) · [06-exam-simulator.md](06-exam-simulator.md) · [11-safety-legal-ethics.md](11-safety-legal-ethics.md)

## Sources
OffSec OSAI Exam FAQ: <https://help.offsec.com/hc/en-us/articles/46669767163156-OSAI-Advanced-AI-Red-Teaming-Exam-FAQ>
