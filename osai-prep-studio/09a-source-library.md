# Source Library — the tutor's grounded corpus

> Purpose: Catalog the curated, cited corpus the tutor retrieves over. The tutor's factual surface is **only** this library; if an answer isn't grounded here, it abstains ([03-tutor-examiner-bot.md](03-tutor-examiner-bot.md), [04-evaluation-harness.md](04-evaluation-harness.md)). No proprietary OffSec course content is ever ingested ([11-safety-legal-ethics.md](11-safety-legal-ethics.md)).

## 1. Corpus principles

1. **Curated, not crawled.** Every source is added deliberately, with metadata and a license note. The tutor does not browse the live web at answer time.
2. **Authority-tiered.** Each source has an authority tier (A0–A5, [03-tutor-examiner-bot.md](03-tutor-examiner-bot.md) §source-authority-tiers); exam claims require an A0 source, framework claims an A1.
3. **Versioned.** Framework sources carry a version + `retrieved_at` and are governed by [15-framework-version-ledger.md](15-framework-version-ledger.md).
4. **No source, no confident answer.** Abstention is a feature, gated at ≥95% in the ship gate.

## 2. Chunk metadata schema

```yaml
chunk:
  source_id: "owasp-llm-top-10-2025"
  title: "OWASP Top 10 for LLM Applications 2025 — LLM01 Prompt Injection"
  url: "https://genai.owasp.org/llm-top-10/"
  authority_tier: "A1"
  owasp_tags: ["LLM01:2025"]
  atlas_tags: ["AML.T0051.000", "AML.T0051.001"]
  nist_tags: ["MEASURE", "MANAGE"]
  license: "CC-BY-SA-4.0"        # or repo-internal MIT, or learner-owned
  retrieved_at: "2026-06-30"
  owner: "content-governance"
  chunk_index: 3                  # 512-token, 10-20% overlap
```

Per-source filtering on these tags enables scoped retrieval (e.g., "only A0 sources for an exam-rule question") and powers citation rendering.

## 3. The catalog

### Tier A1 — public risk/threat frameworks (free to ingest)

| Source | Why it's in the corpus | URL | License note |
|---|---|---|---|
| OWASP Top 10 for LLM Applications (2025) | Canonical LLM risk taxonomy; curriculum spine | <https://genai.owasp.org/llm-top-10/> | OWASP/CC |
| OWASP Agentic AI — Threats and Mitigations | Agentic threat catalog (Track 4) | <https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/> | OWASP/CC |
| OWASP GenAI Red Teaming Guide | Structured AI red-team methodology | <https://genai.owasp.org/resource/genai-red-teaming-guide/> | OWASP/CC |
| MITRE ATLAS | Adversary tactics/techniques for AI; per-finding `AML.Txxxx` | <https://atlas.mitre.org/> | MITRE/ATLAS terms |
| NIST AI RMF 1.0 | Govern/Map/Measure/Manage framing | <https://www.nist.gov/itl/ai-risk-management-framework> | US Gov (public) |
| NIST AI 600-1 GenAI Profile | 12 GenAI risk categories; governance/business translation | <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence> | US Gov (public) |
| NVIDIA AI Kill Chain | Stage model for AI attacks (AI-300 M1) | NVIDIA developer/security blog (pin exact URL at ingest) | vendor doc |

### Tier A0 — OffSec **public** pages only (exam/course facts)

> **Hard rule:** ingest only public marketing/FAQ pages. **Never** ingest paid AI-300 course material, lab guides, or exam content ([11-safety-legal-ethics.md](11-safety-legal-ethics.md)). Each A0 chunk maps to a claim-ledger id ([00b-exam-blueprint.md](00b-exam-blueprint.md)).

| Source | Use for | URL |
|---|---|---|
| AI-300 course page | course scope, 65h, 24h exam, prereqs, OSAI/OSAI+ | <https://www.offsec.com/courses/ai-300/> |
| AI-300 (course) FAQ | 11 modules, leaderboard/XP, access | <https://help.offsec.com/hc/en-us/articles/46593095198740-OSAI-Advanced-AI-Red-Teaming-AI-300-FAQ> |
| OSAI Exam FAQ | exam date, proctoring, AI-use-allowed | <https://help.offsec.com/hc/en-us/articles/46669767163156-OSAI-Advanced-AI-Red-Teaming-Exam-FAQ> |
| LLM Red Teaming path | prereq objectives | <https://www.offsec.com/learning/paths/llm-red-teaming/> |
| OSCP→OSAI blog | pivot framing | <https://www.offsec.com/blog/oscp-to-osai-how-offensive-security-practitioners-can-pivot-into-ai-security/> |

### Tier A2 — tool official docs

PyRIT <https://github.com/microsoft/PyRIT> · garak <https://github.com/NVIDIA/garak> · promptfoo <https://www.promptfoo.dev/docs/red-team/> · Giskard <https://www.giskard.ai/> · RAGAS <https://www.ragas.io/> · DeepEval <https://deepeval.com/>. *Use for:* tool behavior/setup; `ATTACK_WITH_AI` mode guidance.

### Tier A3 — repo-internal seeds (MIT, ours to use)

`../reference/owasp-llm-top-10.md` · `../reference/mitre-atlas.md` · `../reference/owasp-agentic-threats.md` · `../reference/nist-ai-rmf.md` · `../reference/glossary.md` · `../docs/playbook/analyst-runbook.md` · `../docs/llm-log-triage-case-study.pdf` · the studio's own lesson MDX and lab manifests. *These are the highest-precision chunks* — original, tagged, and already mapped to the taxonomy. **Wired into retrieval:** the seven `reference/*.md` files are the tutor's live corpus (`tutor.DEFAULT_SOURCES`); `owasp-agentic-threats.md` (T1–T15), `nist-ai-rmf.md` (RMF functions + the AI 600-1 GenAI risks), `ai-redteam-tooling.md` (PyRIT/garak/promptfoo/Giskard + when-to-use), and `osai-studio-architecture.md` (the studio's own components, trust boundaries, and per-lab attack→detector→defense) were added to ground agentic, NIST, tooling, **architecture_reasoning**, and **lab_grounded** items in the gold set.

### Tier A4 — learner notes vault

The learner's own notes/writeups. *Use for:* personalized study support; **never** as a source for an official claim.

### Tier A5 — community (ideas only)

Blogs, conference talks, write-ups. *Require corroboration from A0–A2 before any fact is treated as authoritative.* Used for lab inspiration, not citations.

## 4. Ingestion notes

512-token recursive chunks with 10–20% overlap (hierarchical small-child/large-parent for long PDFs); dense (pgvector) + BM25 hybrid index; per-source tags for filtered retrieval; re-embed on source version bump. The framework sources' freshness is owned by the monthly update ritual in [20-instructor-ops-runbook.md](20-instructor-ops-runbook.md).

## Cross-references
[03-tutor-examiner-bot.md](03-tutor-examiner-bot.md) · [04-evaluation-harness.md](04-evaluation-harness.md) · [11-safety-legal-ethics.md](11-safety-legal-ethics.md) · [15-framework-version-ledger.md](15-framework-version-ledger.md)
