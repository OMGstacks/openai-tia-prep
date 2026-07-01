"""Per-learner evidence flags (Signal B).

flag = "OSAI{" + HMAC_SHA256(server_seed, learner|lab|attempt)[:24] + "}"

A flag is derived per learner, so a flag shared between learners is worthless —
the anti-cheat property in 02-lab-range.md §A.2 and 21-world-class-additions.md §B4.
Verification is constant-time.
"""

from __future__ import annotations

import hashlib
import hmac

PREFIX = "OSAI{"
SUFFIX = "}"


def _key(server_seed) -> bytes:
    return server_seed.encode() if isinstance(server_seed, str) else bytes(server_seed)


def derive_flag(server_seed, learner_id: str, lab_id: str, attempt: int = 0) -> str:
    msg = f"{learner_id}|{lab_id}|{attempt}".encode()
    digest = hmac.new(_key(server_seed), msg, hashlib.sha256).hexdigest()[:24]
    return f"{PREFIX}{digest}{SUFFIX}"


def verify_flag(server_seed, learner_id: str, lab_id: str, submitted: str, attempt: int = 0) -> bool:
    expected = derive_flag(server_seed, learner_id, lab_id, attempt)
    return hmac.compare_digest(expected, (submitted or "").strip())
