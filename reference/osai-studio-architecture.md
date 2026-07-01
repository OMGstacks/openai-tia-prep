# OSAI Prep Studio — Architecture & Lab Reference

Curated reference for the **OSAI Prep Studio** system's own design — its components,
trust boundaries, grading model, and lab→attack→detector→defense mappings. This grounds
the `architecture_reasoning` and `lab_grounded` gold-set banks: questions about how the
product itself works and about lab evidence are answered and cited from here. Companion
framework docs: [`owasp-llm-top-10.md`](./owasp-llm-top-10.md),
[`owasp-agentic-threats.md`](./owasp-agentic-threats.md), [`nist-ai-rmf.md`](./nist-ai-rmf.md).

## Component ownership
The **grader** owns verdicts: `ChallengeValidator` in `validator.py` performs two-signal
grading. The **engine** (`engine.py`) reuses the flagship `detectors.py` by import — one
detection engine, one taxonomy — extended with three spine detectors, so grading and
lessons share the same `detector_catalog()`. The **tutor** (`tutor.py`) is retrieval-first
and citation-enforced; it never owns grading. The **progress engine** owns XP, badges,
streaks, and spaced repetition. The **report reviewer** (`report.py`) grades written
findings against a business-impact rubric. Each concern lives in one component so the
taxonomy stays the single source of truth.

## Two-signal grading (and Signal C)
A learner passes a lab only when **both** signals hold: **Signal A** is that the reused
detector fires on the attack transcript (the verdict), and **Signal B** is that the attack
physically produced an evidence token — a per-learner HMAC-derived flag, a DB-state
change, or a callback hit — not merely a sentinel string. Agentic labs add **Signal C**, a
causal-chain check that attributes the impact to injected untrusted content rather than
direct user coercion. Requiring produced evidence, not just a model string, is what makes
the auto-grader credible.

## Learner identity and isolation trust boundary
When authentication is enabled, a learner's identity is derived from the **verified session
token subject**, never from a client-supplied id — so a user can only act as themselves.
Flags are **per-learner**, derived by HMAC from a server seed, so one learner's flag never
grades another's submission; this preserves **cross-learner isolation**. Lab-target
containers run on an **internal, egress-denied network** with read-only rootfs, dropped
capabilities, and no-new-privileges, so a compromised target cannot reach the internet or
the host.

## Why the mock target stays in CI and Ollama is deploy-time only
Lab targets use a **deterministic stdlib mock** by default so the full
attack→target→grade loop runs offline and reproducibly in CI with no model and no network.
A real, deliberately weakly-guardrailed **Ollama** model is an opt-in deploy-time realism
upgrade (`OSAI_OLLAMA=1`) behind the identical `.chat()`/`.query()` contract; it is
**non-deterministic**, so it is never the CI default. The backend-agnostic factories
(`make_chat_target` / `make_rag_target` / `make_mcp_target`) keep the grader loop identical
either way.

## Offline-first and opt-in layers
The stdlib **spine core** (taxonomy, flags, manifest, validator) is dependency-free so CI
stays zero-dependency and green with no key. Every richer capability is an opt-in layer
that is **off by default**: the generative LLM tutor (`OSAI_LLM=1`), authentication
(`OSAI_AUTH=1`), secure-cookie mode (`OSAI_COOKIE_AUTH=1`), and real-model targets
(`OSAI_OLLAMA=1`). With none set, behavior is deterministic and offline.

## Data-handling choke point for transcripts
Sending a learner attack transcript to a model is gated behind a **second** opt-in
(`OSAI_LLM_TRANSCRIPTS=1`) and a fail-closed choke point (`datahandling.prepare_for_judging`):
it refuses unless the gate is on **and** the learner has recorded **consent**, then
**redacts** flags/secrets/PII and re-verifies the redaction before any egress, records an
**audit** event (counts only, never content), and retains only redacted transcripts under
a **bounded retention** window that a purge enforces. A premature toggle still cannot send
an unconsented or unredacted transcript.

## Tutor grounding and scope guard
The tutor answers **only from retrieved sources** and **abstains** when the corpus does not
support an answer ("no source, no confident answer"). It validates every OWASP/ATLAS id in
an answer against the taxonomy registry (**no hallucinated ids**), and a **scope guard**
refuses requests to attack real/external/production systems or to reveal lab flags/answer
keys — the authorized-lab-only boundary. These hold with or without the LLM layer.

## Lab range overview
The range is 19 lab manifests (L01–L19) plus the L20 blue-team triage capstone. Each lab
below names the **detector that must fire** (Signal A), the **OWASP category** it
exercises, and the **defense** that stops the attack. The **evidence** that proves any
exploit is the **produced token** (Signal B) — a captured **flag**, a **DB-state change**,
or a **callback-server hit** — not the model's wording.

## Lab L01 — direct prompt injection
Detector: `direct_prompt_injection`. OWASP: LLM01. The learner talks past the guardrail to
exfiltrate the planted flag; evidence is the captured flag. Defense: input filtering and
constrained system-prompt handling.

## Lab L02 — indirect prompt injection via RAG
Detector: `indirect_prompt_injection`. OWASP: LLM01. The learner ingests a poisoned
document; the retrieved document is the untrusted `source=rag` event the grader scans.
Defense: instruction/data **isolation** — never trust retrieved content as instructions.

## Lab L03 — encoded / obfuscated injection
Detector: `encoded_injection_payload`. OWASP: LLM01. A base64/obfuscated payload evades a
naive filter. Defense: decode-then-inspect and canonicalization before filtering.

## Lab L04 — system-prompt extraction
Detector: `system_prompt_extraction`. OWASP: LLM07. The learner coerces the model into
leaking its system prompt. Defense: treat the system prompt as secret; refuse meta-prompts.

## Lab L05 — sensitive-data exfiltration via markdown image
Detector: `improper_output_handling`. OWASP: LLM02 / LLM05. Data is exfiltrated through a
rendered markdown image URL. Defense: **output validation and escaping**, allowlist sinks.

## Lab L06 — improper output handling → XSS / SSRF
Detector: `improper_output_handling`. OWASP: LLM05. Model output reaches an unsafe sink.
Defense: **output validation/escaping** and treating model output as untrusted.

## Lab L07 — sensitive information disclosure
Detector: `sensitive_information_disclosure`. OWASP: LLM02. The model discloses secrets it
should not. Defense: data minimization and output-side redaction.

## Lab L08 — RAG recon & fingerprinting
Detector: `vector_store_probe`. OWASP: LLM08. The learner fingerprints the RAG (embedding
model, chunk size, top-k). Defense: don't reveal retrieval internals; recon-anomaly detection.

## Lab L09 — RAG write-path poisoning
Detector: `indirect_prompt_injection`. OWASP: LLM04 (data poisoning). The learner poisons
the corpus write path. Defense: validate/provenance-check ingested content.

## Lab L10 — vector cross-tenant leak
Detector: `vector_store_probe`. OWASP: LLM08. Retrieval crosses a tenant boundary. Defense:
per-tenant namespaces and access control on the vector store.

## Lab L11 — MCP tool misuse / excessive agency
Detector: `excessive_agency_probe`. OWASP: LLM06; agentic T2 tool misuse. The agent invokes
an over-permissioned tool. Defense: **least-privilege tool scopes + human approval**.

## Lab L12 — MCP tool shadowing / rug-pull
OWASP: LLM06; agentic T9 identity spoofing / tool shadowing. A tool impersonates a trusted
one. Defense: verifiable tool identity and change detection.

## Lab L13 — MCP → remote code execution
Detector: `improper_output_handling` sink. Agentic T11 unexpected RCE. Defense: sandbox
code execution, egress-deny, drop privileges.

## Lab L14 — multi-agent goal manipulation
Grading uses causal-chain **Signal C**. OWASP: LLM09; agentic T5/T6 cascading hallucination
and goal manipulation. Defense: validation between agent hops; grounded, cited outputs.

## Lab L15 — agent memory poisoning
Agentic T1 memory poisoning. Defense: validate what enters memory, integrity-check and
expire stored context.

## Lab L16 — excessive-agency destructive action
Detector: `excessive_agency_probe`. OWASP: LLM06; agentic T3 privilege compromise. Defense:
least privilege and human approval for high-impact actions.

## Lab L17 — supply-chain poisoned adapter
Detector: `supply_chain_trigger`. OWASP: LLM03. A backdoored adapter has a trigger phrase.
Defense: **provenance / SBOM verification** and signed artifacts.

## Lab L18 — cloud / model-server SSRF
Detector: `unbounded_consumption_probe`. OWASP: LLM10. SSRF reaches an internal inference
endpoint. Defense: network segmentation and egress control.

## Lab L19 — model extraction / denial-of-wallet
Detector: `unbounded_consumption_probe`. OWASP: LLM10; agentic T4 resource overload. A query
campaign clones the model / runs up the bill. Defense: **rate and budget caps**, quotas.

## Lab L20 — blue-team triage capstone
Triage the incident log against the full detector catalog; the deliverable is an
OffSec-style **report**. Exercises the defensive/reporting view across the taxonomy.
