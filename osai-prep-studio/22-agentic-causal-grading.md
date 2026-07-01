# Agentic Causal-Chain Grading (design — next content phase)

> Purpose: capture the SOTA direction for grading agentic exploits beyond "did the
> learner extract the flag." Design-only; sequenced after the auth/deploy hardening and
> the merge. Extends the two-signal `ChallengeValidator` ([02-lab-range.md](02-lab-range.md) §A.2),
> not replaces it.

## 1. Why flag-extraction grading is not enough

Today a lab passes on **two signals**: the reused detector fires (Signal A) *and* the
attacker produces an evidence token (Signal B). That proves *an* exploit occurred, but it
doesn't grade the **causal quality** of the attack — the thing that separates a red-teamer
from someone who got lucky. For agentic/MCP/RAG labs especially, the interesting question
is *why* a tool call happened: was it driven by the user's intent, or hijacked by
untrusted content?

Recent agent-security research reframes indirect prompt-injection defense as
**action-level causal attribution** rather than string matching:

- **AttriGuard** — attribute each tool invocation to its cause: is the call *supported by
  the user's intent* or *causally driven by untrusted tool/RAG output*? A call with no
  intent support is the injection.
- **AgentSentry** — treat multi-turn indirect injection as a **temporal causal takeover**;
  use counterfactual re-execution around tool-return boundaries to test whether removing
  the untrusted content changes the action.

The world-class enhancement: grade the **full chain**, not the endpoint —
`user intent → untrusted content → model reasoning → tool call → evidence → mitigation`.

## 2. Signal C — the causal chain (proposed)

Add an optional third signal for agentic labs, scored from the run's **structured
telemetry** (the logging plane already emits canonical events). A lab manifest may
declare a `causal_chain` spec; the grader reconstructs the chain and scores each hop:

| Hop | What we check | Telemetry source |
|---|---|---|
| **intent** | the learner's stated objective vs the benign user turn | attack transcript |
| **injection point** | untrusted content (rag/tool/web/email) carried the imperative | source-tagged events |
| **causal link** | the offending tool call is *attributable to* the untrusted content, not the user (counterfactual: remove it → action disappears) | tool-call log + re-exec oracle |
| **evidence** | the produced token / DB-state / callback (Signal B) | flag/callback/db-state |
| **mitigation** | the learner's report names the correct control (trust boundary / least-privilege / I-O gate) | report reviewer |

Pass grade = a **connected** chain, not just a fired detector. This makes "solved by
pattern-matching a payload" fail where "understood and reproduced the causal takeover"
passes.

## 3. Counterfactual oracle (lab-side)

For MCP/agent labs the target already logs tool calls. Add a deterministic
**re-execution oracle**: replay the run with the untrusted content *neutralized*
(stripped/delimited-as-data). If the offending tool call no longer fires, the original
call is **causally attributed** to the injection → Signal C confirmed. This is offline
and deterministic (no model needed for the mock targets; with an Ollama target it runs
twice and compares tool-call sets).

## 4. Telemetry to add (per [05-progress-engine.md](05-progress-engine.md) analytics)

Grade and record, per attempt:
`tool_call_authorized`, `user_intent_mismatch`, `rag_source_poisoned`,
`multi_turn_takeover`, `mcp_boundary_abuse`, `external_egress_attempt`,
`credential_in_tool_context`, `unsafe_autonomous_action`. These become new **skill tags**
on the shared taxonomy → they route to the SRS and the readiness model like any other tag.

## 5. Attack↔defense pairing (every offensive lab ends blue)

Make each agentic lab's *report* require a **detection-engineering** deliverable: the
learner writes the query/rule that would have caught the causal takeover (mirrors the L20
capstone at a per-lab scale). Graded by the report reviewer against a mitigation rubric.

## 6. Build sequence (when greenlit)

1. Manifest schema: optional `causal_chain` block (hops + expected attribution).
2. `causal.py`: chain reconstruction from telemetry + the counterfactual oracle.
3. Extend `ChallengeValidator` with an optional Signal C (labs without a `causal_chain`
   are unaffected — additive, like auth/LLM).
4. New skill tags in the taxonomy registry + SRS wiring.
5. Pilot on L11 (MCP tool misuse) and L14 (multi-agent goal manipulation).

## Sources
- OWASP LLM01 Prompt Injection (direct vs indirect): <https://genai.owasp.org/llmrisk/llm01-prompt-injection/>
- AttriGuard — causal attribution of tool invocations (indirect prompt injection defense).
- AgentSentry — temporal causal diagnostics for multi-turn indirect injection.
- MITRE ATLAS `AML.T0051.001` (LLM Prompt Injection: Indirect).

## Cross-references
[02-lab-range.md](02-lab-range.md) (two-signal grading) ·
[04-evaluation-harness.md](04-evaluation-harness.md) ·
[05-progress-engine.md](05-progress-engine.md) ·
[16-attack-path-graphs.md](16-attack-path-graphs.md)
