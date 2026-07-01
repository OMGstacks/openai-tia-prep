"""Stale / version-sensitive claim detection (Bank Expansion Epic Phase 3).

AI-security frameworks move fast, and the studio's own state changes, so a claim that was
true last year can be wrong today. This module flags **stale claims** against the current
ground truth (the framework version ledger, 15-framework-version-ledger.md, plus the
studio's own facts) and names the fresher fact, so the tutor can caveat rather than repeat
an outdated claim. Rule-based and stdlib-only — deterministic, no model needed.

``check_claim(text)`` returns ``{"stale", "fresher", "guidance"}``:
  * ``stale``   — True if the claim matches a known-outdated pattern;
  * ``fresher`` — the corrected/current fact to cite (None when not stale);
  * ``guidance``— what the tutor should do: ``"caveat"`` a stale claim, else ``"answer"``.
"""

from __future__ import annotations

import re

# (pattern, fresher-fact). Each pattern matches a claim that is outdated or wrong given the
# CURRENT ground truth; the fresher fact is what the tutor should cite instead. Kept small
# and high-confidence — only claims we can correct accurately.
_STALE_RULES: list[tuple[re.Pattern, str]] = [
    # OWASP LLM Top 10 is the 2025 revision.
    (re.compile(r"\bowasp\b.{0,40}\bllm\b.{0,20}\b(20)?(23|24)\b", re.I),
     "The current OWASP Top 10 for LLM Applications is the 2025 revision (LLM01:2025–LLM10:2025)."),
    (re.compile(r"\b(latest|current|newest)\b.{0,30}\bowasp\b.{0,30}\bllm\b.{0,30}\b(20)?(23|24)\b", re.I),
     "The current OWASP LLM Top 10 is the 2025 revision, not 2023/2024."),
    # Excessive Agency was LLM08 in the 2023 list; in 2025 it is LLM06.
    (re.compile(r"\bllm-?0?8\b.{0,30}\bexcessive\s+agency\b|\bexcessive\s+agency\b.{0,30}\bllm-?0?8\b", re.I),
     "In OWASP 2025, Excessive Agency is LLM06:2025 (it was LLM08 in the 2023 list)."),
    # System Prompt Leakage is new in 2025 as LLM07.
    (re.compile(r"\bsystem\s+prompt\s+leakage\b.{0,40}\bnot\b.{0,20}\bowasp\b", re.I),
     "System Prompt Leakage is LLM07:2025 — a category added in the 2025 OWASP LLM Top 10."),
    # The studio is offline-first: CI never needs a live LLM / key.
    (re.compile(r"\b(ci|continuous integration|test suite|tests?)\b.{0,40}\b(require|need)s?\b.{0,40}"
                r"\b(live|real)?\s*(llm|model|api key|anthropic key)\b", re.I),
     "CI is offline-first: it is green with no key and no model; the LLM layer is opt-in (OSAI_LLM=1) and its tests auto-skip when absent."),
    (re.compile(r"\b(live|real)\s+(llm|model|api key)\b.{0,30}\b(required|needed|necessary)\b.{0,30}\b(ci|tests?)\b", re.I),
     "A live LLM is NOT required for CI — the spine core is stdlib-only and deterministic."),
    # The gold set is no longer four banks.
    (re.compile(r"\b(only|just)\s+(four|4)\b.{0,30}\bbanks?\b|\bgold[- ]?set\b.{0,20}\b(four|4)\s+banks?\b", re.I),
     "The gold set now has 7+ graded banks (framework_recall, abstention, refusal, lab_answer_leakage, architecture_reasoning, lab_grounded, tool_use_judgment, …)."),
    # 750 is not reachable by padding.
    (re.compile(r"\b750\b.{0,40}\b(pad|padding|recall)\b|\b(pad|padding)\b.{0,40}\b750\b", re.I),
     "~750 is reached by building new grader-backed bank types, not by padding recall/refusal near-duplicates."),
    # Prompt injection is the current #1 (LLM01), not a lesser/older ranking.
    (re.compile(r"\bprompt\s+injection\b.{0,30}\bllm-?0?[2-9]\b|\bllm-?0?[2-9]\b.{0,30}\bprompt\s+injection\b", re.I),
     "Prompt Injection is LLM01:2025 (the top category) in the current OWASP LLM Top 10."),
]


def check_claim(text: str) -> dict:
    """Return a staleness verdict for a claim. See module docstring."""
    q = text or ""
    for pattern, fresher in _STALE_RULES:
        if pattern.search(q):
            return {"stale": True, "fresher": fresher, "guidance": "caveat"}
    return {"stale": False, "fresher": None, "guidance": "answer"}
