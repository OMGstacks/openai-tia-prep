# Safety, Legality & Ethics (content policy)

> Purpose: The content and conduct boundary for the studio and its tutor. This is the *policy* layer; the *infrastructure* threat model (container escape, isolation, egress) lives in [13-platform-threat-model.md](13-platform-threat-model.md).

## 1. Core boundary — authorized-lab-only

OSAI Prep Studio is an **authorized lab and certification-prep platform**. The platform, its labs, and its tutor operate **only** against the local/authorized range. They never target real, named, or external systems.

- All exploitation happens against the Dockerized MegacorpAI range ([02-lab-range.md](02-lab-range.md)).
- All planted secrets are **fake, non-production** values.
- The tutor refuses to help attack anything outside the current authorized lab.

## 2. Tutor refusal policy

The tutor (and exam-sim/report-reviewer modes) **refuses**:
- requests to attack public, real, or named external systems;
- requests to steal real data, bypass real accounts, or exploit live organizations;
- requests that produce real-world harm — including CBRN/cyber-physical uplift — mirroring NIST AI 600-1 dangerous-capability gating.

The tutor **may**:
- explain vulnerabilities and methodology as applied to the provided lab targets;
- run/coach against local labs;
- help write professional reports.

This is enforced by the scope-guard (pre-retrieval) and validated by the `refusal` + `tutor_self_redteam` gold-set banks at **100%** ([04-evaluation-harness.md](04-evaluation-harness.md)). The line is *operational vs educational*: teach the technique against the lab; refuse to aim it at the world.

## 3. Intellectual-property boundary

- Use only **public** OffSec pages for high-level alignment (course/FAQ/blog — Tier A0, [09a-source-library.md](09a-source-library.md)).
- Use OWASP / NIST / MITRE / public frameworks, the learner's own notes, and the studio's **original** explanations and labs.
- **Never** copy, paraphrase at length, ingest, or redistribute proprietary AI-300 course material, lab guides, or exam content. Once a learner owns AI-300, the tutor may help them study **their own** notes — it must not redistribute OffSec's material.
- The studio's labs are **original** and merely *complement* public deliberately-vulnerable apps (Gandalf, DVMCP, AI Goat, PortSwigger) — they do not copy them.

## 4. Learner data handling & privacy

- Minimize collected data; store progress under the learner's account only.
- Notes vault (Tier A4) is private to the learner and never used for official claims or shared retrieval.
- Hash AI-use events and prompts where logged ([18-ai-use-policy-for-exam-mode.md](18-ai-use-policy-for-exam-mode.md)); no third-party sharing of learner transcripts.
- Local-first model routing for routine turns keeps most learner content on-device/in-range ([07-architecture-and-stack.md](07-architecture-and-stack.md)).

## 5. Responsible-disclosure ethos (taught, not just enforced)

Track 6 teaches the professional ethic alongside the technical skill: scope/authorization before testing, rules of engagement, evidence handling, coordinated disclosure, and "do no harm." The studio models the behavior it teaches — a red teamer who can't operate ethically and within authorization is not employable. The **rules-of-engagement / authorization workflow** learners practice producing is specified in [21-world-class-additions.md](21-world-class-additions.md).

## 6. Acceptable-use policy (platform)

Learners agree to: use the platform only for authorized learning; not point studio tooling at systems they don't own or aren't authorized to test; not attempt to extract other learners' flags or data; not use the tutor to generate real-world attack assistance. Violations disable lab access. The platform's own abuse controls (egress deny-all, per-learner isolation, flag integrity) are in [13-platform-threat-model.md](13-platform-threat-model.md).

## Cross-references
[03-tutor-examiner-bot.md](03-tutor-examiner-bot.md) · [04-evaluation-harness.md](04-evaluation-harness.md) · [09a-source-library.md](09a-source-library.md) · [13-platform-threat-model.md](13-platform-threat-model.md) · [18-ai-use-policy-for-exam-mode.md](18-ai-use-policy-for-exam-mode.md)

## Sources
- NIST AI 600-1 GenAI Profile: <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence>
- OWASP GenAI Red Teaming Guide: <https://genai.owasp.org/resource/genai-red-teaming-guide/>
