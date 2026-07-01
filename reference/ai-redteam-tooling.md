# AI Red-Team Tooling — PyRIT, garak, promptfoo, Giskard

Quick reference for the open-source tools an AI red-teamer uses to *automate* attacks and
evaluations ("attack with AI"). Each entry: what it is, what it's best at, and when to
reach for it. Companion docs: [`owasp-llm-top-10.md`](./owasp-llm-top-10.md),
[`mitre-atlas.md`](./mitre-atlas.md), [`owasp-agentic-threats.md`](./owasp-agentic-threats.md),
[`nist-ai-rmf.md`](./nist-ai-rmf.md), [`glossary.md`](./glossary.md).

Sources: PyRIT <https://github.com/Azure/PyRIT> · garak <https://github.com/NVIDIA/garak> ·
promptfoo <https://www.promptfoo.dev/docs/red-team/> · Giskard <https://www.giskard.ai/>.

## PyRIT
**PyRIT** (Python Risk Identification Toolkit, Microsoft) is a framework for *automating*
generative-AI red-teaming. It composes an **orchestrator** that drives an attacker
strategy against a **target**, with **converters** (encode/translate/obfuscate a payload)
and **scorers** (judge whether an attempt succeeded). It supports multi-turn, adaptive
attack campaigns. **Best at / when to use:** programmable, repeatable attack campaigns —
especially multi-turn jailbreaks and payload-mutation sweeps you want to script and rerun.

## garak
**garak** (NVIDIA) is an **LLM vulnerability scanner** — think "nmap for LLMs." It runs a
library of **probes** (prompt injection, jailbreak, hallucination/misinformation,
toxicity, data leakage, encoding attacks) paired with **detectors** that flag failures,
and emits a report. It is CLI-driven and model-agnostic. **Best at / when to use:** a fast,
broad first-pass scan to find low-hanging vulnerabilities across many categories before you
invest in targeted manual work.

## promptfoo
**promptfoo** is an evaluation and red-team framework built around **test cases with
assertions**. Its red-team feature auto-generates adversarial inputs, and it ships
**OWASP LLM Top 10 and NIST AI RMF presets**. It runs well in CI and produces
side-by-side/regression views. **Best at / when to use:** turning findings into a
**regression suite** and gating changes in CI, and preset-driven coverage of OWASP/NIST
categories. (This studio's own gold-set gate follows the same philosophy.)

## Giskard
**Giskard** is an ML/LLM **testing and vulnerability-scanning** framework. It scans a model
or RAG app for issues (prompt injection, harmfulness, robustness, hallucination, sensitive
disclosure) and generates test suites. **Best at / when to use:** pre-deployment quality +
vulnerability scanning of a specific application, and building a persistent test suite
around it.

## Choosing a tool (and when to go manual)
- **Broad automated scan, fast** → **garak** (many probes, one command).
- **Scripted multi-turn / mutation attack campaign** → **PyRIT** (orchestrator + converters + scorers).
- **Regression eval + CI gate, OWASP/NIST presets** → **promptfoo**.
- **App-specific vulnerability scan + reusable test suite** → **Giskard**.
- **Novel logic flaws, business-logic abuse, chained/agentic exploits** → **manual testing**;
  automated scanners find known categories, not the bespoke bug. Use the tools to clear the
  known surface quickly, then spend human time where they can't reach.
