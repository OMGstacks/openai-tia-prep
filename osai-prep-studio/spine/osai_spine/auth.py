"""Optional authentication (opt-in via ``OSAI_AUTH=1``) — stdlib only, hardened.

Off by default, so the offline/demo/CI flows (learner id supplied in the request) are
unchanged. When enabled, learner-scoped endpoints derive the learner from a verified
**session token** rather than a client-supplied id, so a user can only act as
themselves.

Hardening (OWASP Password Storage / Session Management, NIST 800-63B):
  * PBKDF2-HMAC-SHA256, **600k iterations**, per-user random salt, stored in a
    self-describing PHC-style string (``pbkdf2_sha256$iters$salt$hash``) so the cost
    factor can rise over time — and login transparently **rehashes** stale hashes;
  * stateless HMAC-signed tokens carry ``sub/iat/exp/jti/ver`` and are verified with a
    constant-time compare; a per-user ``session_version`` (``ver``) gives **revocation**
    (logout / password change bump it, invalidating every outstanding token);
  * login **throttling** (per-username sliding window) blunts online brute force;
  * a **fail-closed deploy guard** (``enforce_deploy_policy``) refuses to start a public
    deployment (``OSAI_PUBLIC=1``) unless auth is on with a strong, non-default secret.

Passwords are never stored in plaintext and never leave the server; tokens carry no
secret material.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
from collections import deque

_TRUTHY = {"1", "true", "on", "yes"}

ALGO = "pbkdf2_sha256"
PBKDF2_ITERS = 600_000          # OWASP recommendation for PBKDF2-HMAC-SHA256 (FIPS)
TOKEN_TTL = 12 * 3600           # seconds; revocation via session_version covers early logout
MIN_PASSWORD_LEN = 12
DEFAULT_SECRET = "dev-auth-secret-change-me"
MIN_SECRET_LEN = 32

# Login throttle: at most this many failures per username per window.
LOGIN_MAX_FAILURES = 5
LOGIN_WINDOW_S = 300.0


SESSION_COOKIE = "osai_session"
CSRF_COOKIE = "osai_csrf"


def auth_enabled() -> bool:
    return os.environ.get("OSAI_AUTH", "").strip().lower() in _TRUTHY


def cookie_auth_enabled() -> bool:
    """Opt-in production cookie session mode (HttpOnly/Secure/SameSite + CSRF) instead
    of Bearer-in-localStorage. Requires auth. Bearer mode stays the default for API
    clients / local dev."""
    return auth_enabled() and os.environ.get("OSAI_COOKIE_AUTH", "").strip().lower() in _TRUTHY


def cookie_secure() -> bool:
    """Cookies carry the Secure flag by default (HTTPS-only). Set OSAI_COOKIE_SECURE=0
    only for local HTTP testing."""
    return os.environ.get("OSAI_COOKIE_SECURE", "1").strip().lower() in _TRUTHY


def new_csrf() -> str:
    """A fresh random CSRF token for the double-submit-cookie pattern."""
    return _b64e(os.urandom(18))


def _admin_users() -> set:
    """Usernames granted the ``instructor`` role at registration — bootstrapped from
    ``OSAI_ADMIN_USERS`` (comma-separated). Simple, explicit, no self-promotion path."""
    return {u.strip() for u in os.environ.get("OSAI_ADMIN_USERS", "").split(",") if u.strip()}


def read_secret(env=None) -> str:
    """Resolve the token-signing secret, preferring a Docker-secret **file**
    (``OSAI_AUTH_SECRET_FILE``, e.g. ``/run/secrets/osai_auth_secret``) over the
    inline ``OSAI_AUTH_SECRET`` env var — the same file-first convention the LLM key
    uses, so the secret never has to live in the host/container process environment.
    Returns ``""`` if neither is set (callers fall back to ``DEFAULT_SECRET``)."""
    env = env if env is not None else os.environ
    path = (env.get("OSAI_AUTH_SECRET_FILE") or "").strip()
    if path:
        try:
            with open(path, encoding="utf-8-sig") as fh:
                val = fh.read().strip()
            if val:
                return val
        except OSError:
            pass
    return env.get("OSAI_AUTH_SECRET", "") or ""


class AuthError(Exception):
    """Registration/validation failure (bad input, duplicate user)."""


class LoginThrottled(Exception):
    """Too many failed logins for a username within the window."""


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(txt: str) -> bytes:
    return base64.urlsafe_b64decode(txt + "=" * (-len(txt) % 4))


def _encode_password(password: str, salt: bytes | None = None, iters: int = PBKDF2_ITERS) -> str:
    salt = salt if salt is not None else os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iters)
    return f"{ALGO}${iters}${_b64e(salt)}${_b64e(dk)}"


def _verify_password(password: str, encoded: str):
    """Return (ok, needs_rehash). ``needs_rehash`` is True when the stored cost is below
    the current policy, so a correct login can upgrade the stored hash."""
    try:
        algo, iters_s, salt_b64, hash_b64 = encoded.split("$")
        iters = int(iters_s)
    except Exception:
        return False, False
    if algo != ALGO:
        return False, False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), _b64d(salt_b64), iters)
    ok = hmac.compare_digest(_b64e(dk), hash_b64)
    return ok, (ok and iters < PBKDF2_ITERS)


_DUMMY_HASH = None


def _dummy_hash() -> str:
    """A cached hash to verify against when the user doesn't exist, so login timing
    doesn't reveal whether a username is registered (user-enumeration side channel).
    Computed lazily to keep import cheap."""
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = _encode_password("timing-equalizer-not-a-real-password")
    return _DUMMY_HASH


def enforce_deploy_policy(env=None) -> None:
    """Fail closed on a public deployment that isn't secured. No-op unless
    ``OSAI_PUBLIC=1``; then auth must be on with a strong, non-default secret, unless
    ``OSAI_ALLOW_INSECURE_PUBLIC_DEMO=1`` is set."""
    env = env if env is not None else os.environ
    if env.get("OSAI_PUBLIC", "").strip().lower() not in _TRUTHY:
        return
    if env.get("OSAI_ALLOW_INSECURE_PUBLIC_DEMO", "").strip().lower() in _TRUTHY:
        return
    problems = []
    if env.get("OSAI_AUTH", "").strip().lower() not in _TRUTHY:
        problems.append("set OSAI_AUTH=1")
    secret = read_secret(env)
    if not secret or secret == DEFAULT_SECRET:
        problems.append("set OSAI_AUTH_SECRET (or OSAI_AUTH_SECRET_FILE) to a non-default value")
    elif len(secret) < MIN_SECRET_LEN:
        problems.append(f"the auth secret must be >= {MIN_SECRET_LEN} chars")
    if problems:
        raise RuntimeError(
            "refusing to start a public deployment (OSAI_PUBLIC=1) without: "
            + "; ".join(problems)
            + " — or set OSAI_ALLOW_INSECURE_PUBLIC_DEMO=1 for a demo."
        )


class _LoginThrottle:
    """Per-username sliding-window failed-login limiter (in-process)."""

    def __init__(self, max_failures=LOGIN_MAX_FAILURES, window_s=LOGIN_WINDOW_S):
        self.max_failures = max_failures
        self.window_s = window_s
        self._fails: dict[str, deque] = {}

    def check(self, username: str, now: float) -> bool:
        dq = self._fails.get(username)
        if not dq:
            return True
        while dq and now - dq[0] >= self.window_s:
            dq.popleft()
        return len(dq) < self.max_failures

    def record_failure(self, username: str, now: float) -> None:
        self._fails.setdefault(username, deque()).append(now)

    def clear(self, username: str) -> None:
        self._fails.pop(username, None)


class AuthStore:
    """SQLite-backed user store + stateless token issuer/verifier (hardened)."""

    def __init__(self, db_path: str = ":memory:", secret: str | None = None):
        self.secret = (secret or read_secret() or DEFAULT_SECRET).encode()
        self._lock = threading.Lock()
        self._throttle = _LoginThrottle()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS user ("
                "  username        TEXT PRIMARY KEY,"
                "  pw              TEXT NOT NULL,"
                "  role            TEXT NOT NULL DEFAULT 'learner',"
                "  session_version INTEGER NOT NULL DEFAULT 0,"
                "  created_ts      REAL NOT NULL)"
            )
            self.conn.commit()

    # --- accounts ----------------------------------------------------------
    def register(self, username: str, password: str, now: float | None = None) -> str:
        username = (username or "").strip()
        if not username or len(username) > 64:
            raise AuthError("username required (<= 64 chars)")
        if not password or len(password) < MIN_PASSWORD_LEN:
            raise AuthError(f"password must be at least {MIN_PASSWORD_LEN} characters")
        now = float(now) if now is not None else time.time()
        encoded = _encode_password(password)
        role = "instructor" if username in _admin_users() else "learner"
        with self._lock:
            try:
                self.conn.execute(
                    "INSERT INTO user(username,pw,role,session_version,created_ts) VALUES(?,?,?,0,?)",
                    (username, encoded, role, now),
                )
                self.conn.commit()
            except sqlite3.IntegrityError:
                raise AuthError("username already taken")
        return username

    def role(self, username: str) -> str:
        row = self.conn.execute("SELECT role FROM user WHERE username=?", (username,)).fetchone()
        return row["role"] if row else "learner"

    def is_instructor(self, username: str) -> bool:
        return self.role(username) == "instructor"

    def usernames(self) -> list:
        return sorted(
            r["username"] for r in self.conn.execute("SELECT username FROM user").fetchall()
        )

    def verify_password(self, username: str, password: str) -> bool:
        row = self.conn.execute("SELECT pw FROM user WHERE username=?", (username,)).fetchone()
        # verify against a dummy hash for unknown users so timing doesn't leak existence
        ok, _rehash = _verify_password(password or "", row["pw"] if row else _dummy_hash())
        return ok if row else False

    def authenticate(self, username: str, password: str, now: float | None = None) -> bool:
        """Verify + throttle + rehash-on-login. Raises ``LoginThrottled`` when the
        per-username failure window is exhausted."""
        now = float(now) if now is not None else time.time()
        if not self._throttle.check(username, now):
            raise LoginThrottled("too many failed attempts; try again later")
        row = self.conn.execute("SELECT pw FROM user WHERE username=?", (username,)).fetchone()
        # verify against a dummy hash for unknown users so login timing is constant
        ok, needs_rehash = _verify_password(password or "", row["pw"] if row else _dummy_hash())
        if not row:
            ok = False
        if not ok:
            self._throttle.record_failure(username, now)
            return False
        self._throttle.clear(username)
        if needs_rehash:  # transparently upgrade the stored cost factor
            with self._lock:
                self.conn.execute(
                    "UPDATE user SET pw=? WHERE username=?", (_encode_password(password), username)
                )
                self.conn.commit()
        return True

    def _session_version(self, username: str):
        row = self.conn.execute(
            "SELECT session_version FROM user WHERE username=?", (username,)
        ).fetchone()
        return row["session_version"] if row else None

    def revoke_sessions(self, username: str) -> None:
        """Bump the session version — every outstanding token for the user is now
        invalid (logout / password change)."""
        with self._lock:
            self.conn.execute(
                "UPDATE user SET session_version = session_version + 1 WHERE username=?",
                (username,),
            )
            self.conn.commit()

    # --- tokens ------------------------------------------------------------
    def issue_token(self, username: str, ttl: int = TOKEN_TTL, now: float | None = None) -> str:
        now = float(now) if now is not None else time.time()
        payload = {
            "sub": username,
            "iat": now,
            "exp": now + ttl,
            "jti": _b64e(os.urandom(9)),
            "ver": self._session_version(username) or 0,
        }
        body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
        sig = _b64e(hmac.new(self.secret, body.encode(), hashlib.sha256).digest())
        return f"{body}.{sig}"

    def verify_token(self, token: str, now: float | None = None):
        """Return the username for a valid, unexpired, non-revoked token, else ``None``."""
        now = float(now) if now is not None else time.time()
        try:
            body, sig = (token or "").split(".", 1)
        except ValueError:
            return None
        expected = _b64e(hmac.new(self.secret, body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        try:
            payload = json.loads(_b64d(body))
        except Exception:
            return None
        if float(payload.get("exp", 0)) < now:
            return None
        sub = payload.get("sub")
        if payload.get("ver") != self._session_version(sub):  # revoked / stale session
            return None
        return sub
