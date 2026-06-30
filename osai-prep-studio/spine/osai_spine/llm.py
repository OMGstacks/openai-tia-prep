"""LLM provider seam — the model router from 07-architecture-and-stack.md.

**Optional.** The platform runs fully offline without it: the tutor falls back to
its extractive answer and lab targets to the deterministic mocks, so CI is green
with no key and no network. When the operator sets ``ANTHROPIC_API_KEY`` *and*
installs the official ``anthropic`` SDK *and* opts in with ``OSAI_LLM=1``, this
wires the highest-quality paths (the grounded tutor answer first) to Claude.

The key is read from the environment ONLY — never hardcoded, never logged.

Defaults follow the project's model recommendation:
  * ``claude-opus-4-8`` for the quality paths (grounded tutor answers, report-judge
    prose grading, Socratic depth) — the best-experience default;
  * a cheaper ``claude-haiku-4-5`` tier for high-volume generation (flashcards,
    scenario assembly);
  * adaptive thinking, streaming via ``get_final_message()``, and prompt caching on
    the fixed retrieved-corpus prefix.

Both model ids are overridable via ``OSAI_LLM_MODEL`` / ``OSAI_LLM_MODEL_BULK``.
"""

from __future__ import annotations

import os
import re

# Quality tier (default) and bulk tier (cheap, high-volume) — overridable via env.
MODEL_QUALITY = os.environ.get("OSAI_LLM_MODEL", "claude-opus-4-8")
MODEL_BULK = os.environ.get("OSAI_LLM_MODEL_BULK", "claude-haiku-4-5")

_TRUTHY = {"1", "true", "on", "yes"}

# Patterns scrubbed before any learner content leaves the box (defense in depth — the
# range plants only fake secrets, but the API call must not carry tokens/PII anyway).
# See docs/security/api-key-and-data-handling.md.
_REDACTIONS = [
    (re.compile(r"OSAI\{[^}]*\}"), "[REDACTED_FLAG]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"\bsk-[A-Za-z0-9._-]{16,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
                re.S), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[REDACTED_PAN]"),
]


def sdk_available() -> bool:
    """True iff the official anthropic SDK can be imported."""
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:  # pragma: no cover - depends on the install env
        return False


def key_present() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def enabled() -> bool:
    """The generative layer is OFF unless explicitly opted in AND actually usable.
    This keeps the default, no-key experience deterministic and offline. Governs the
    low-risk tutor path (query + public reference corpus)."""
    opted_in = os.environ.get("OSAI_LLM", "").strip().lower() in _TRUTHY
    return opted_in and key_present() and sdk_available()


def transcripts_enabled() -> bool:
    """A SECOND, separate opt-in gate for paths that would send *learner attack
    transcripts* to the API (report-judge, attacker-LLM). Requires the base gate AND
    an explicit OSAI_LLM_TRANSCRIPTS=1. Held OFF until the data-handling controls in
    docs/security/api-key-and-data-handling.md are in place; even then, content is
    redacted first (see ``redact_transcript``)."""
    opted_in = os.environ.get("OSAI_LLM_TRANSCRIPTS", "").strip().lower() in _TRUTHY
    return enabled() and opted_in


def redact_text(text: str) -> str:
    """Scrub flags / secrets / PII from a string before it can leave the box."""
    for pattern, repl in _REDACTIONS:
        text = pattern.sub(repl, text or "")
    return text


def redact_transcript(transcript) -> list:
    """Return a copy of a transcript with every event's content redacted. The learner-
    content LLM paths MUST pass transcripts through this before any API call."""
    out = []
    for event in transcript or []:
        ev = dict(event)
        ev["content"] = redact_text(ev.get("content", ""))
        out.append(ev)
    return out


def status() -> dict:
    """A small introspection blob for /health so the operator can see whether their
    key is live without leaking it. Never includes the value/prefix/suffix/length."""
    return {
        "enabled": enabled(),
        "transcripts_enabled": transcripts_enabled(),
        "sdk_installed": sdk_available(),
        "key_present": key_present(),
        "model_quality": MODEL_QUALITY,
        "model_bulk": MODEL_BULK,
    }


class LLMProvider:
    """Thin wrapper over the Anthropic Messages API. Constructed only when the seam
    is enabled; callers always wrap ``complete`` with their own offline fallback."""

    def __init__(self, model: str | None = None):
        self.model = model or MODEL_QUALITY
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        return self._client

    def complete(self, system: str, user: str, *, model: str | None = None,
                 max_tokens: int = 700, cached_prefix: str | None = None) -> str:
        """One grounded completion. ``cached_prefix`` is a large fixed context block
        (e.g. the retrieved corpus) marked for prompt caching so repeat calls over
        the same sources are cheap. Streams (adaptive thinking can run long) and
        returns the final assistant text. Raises on API error."""
        system_blocks = [{"type": "text", "text": system}]
        if cached_prefix:
            system_blocks.append({
                "type": "text",
                "text": cached_prefix,
                "cache_control": {"type": "ephemeral"},
            })
        with self.client.messages.stream(
            model=model or self.model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=system_blocks,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        return "".join(
            block.text for block in msg.content
            if getattr(block, "type", None) == "text"
        ).strip()
