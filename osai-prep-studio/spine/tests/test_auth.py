"""Hardened auth core: PBKDF2 (600k, self-describing, rehash-on-login), revocable
signed tokens, login throttle, and the fail-closed deploy guard."""

import pytest

from osai_spine.auth import (
    AuthError,
    AuthStore,
    LoginThrottled,
    _encode_password,
    auth_enabled,
    enforce_deploy_policy,
    read_secret,
)


def _store():
    return AuthStore(secret="test-secret-value-at-least-32-chars!!")


def test_register_and_verify_password():
    s = _store()
    s.register("alice", "correct-horse-battery")
    assert s.verify_password("alice", "correct-horse-battery") is True
    assert s.verify_password("alice", "wrong-password-here") is False
    assert s.verify_password("nobody", "whatever-password") is False


def test_password_stored_as_self_describing_hash():
    s = _store()
    s.register("alice", "correct-horse-battery")
    pw = s.conn.execute("SELECT pw FROM user WHERE username='alice'").fetchone()["pw"]
    assert pw.startswith("pbkdf2_sha256$600000$")  # algorithm + cost are recorded
    assert "correct-horse-battery" not in pw       # never plaintext


def test_register_rejects_bad_input():
    s = _store()
    with pytest.raises(AuthError):
        s.register("alice", "short")            # < 12 chars
    with pytest.raises(AuthError):
        s.register("", "long-enough-password")  # empty username
    s.register("bob", "long-enough-password")
    with pytest.raises(AuthError):
        s.register("bob", "another-good-password")  # duplicate


def test_authenticate_and_rehash_on_login():
    s = _store()
    # simulate a stale, low-cost hash in the DB
    s.conn.execute(
        "INSERT INTO user(username,pw,session_version,created_ts) VALUES('carol',?,0,0)",
        (_encode_password("passphrase-1234", iters=1000),),
    )
    s.conn.commit()
    assert s.authenticate("carol", "passphrase-1234") is True
    upgraded = s.conn.execute("SELECT pw FROM user WHERE username='carol'").fetchone()["pw"]
    assert upgraded.split("$")[1] == "600000"       # cost factor transparently upgraded
    assert s.authenticate("carol", "wrong") is False


def test_login_throttle_blocks_then_recovers():
    s = _store()
    s.register("dave", "passphrase-1234")
    for i in range(5):
        assert s.authenticate("dave", "wrong", now=1000.0 + i) is False
    with pytest.raises(LoginThrottled):
        s.authenticate("dave", "wrong", now=1000.0 + 5)      # window exhausted
    assert s.authenticate("dave", "passphrase-1234", now=2000.0) is True  # window slid


def test_token_roundtrip_expiry_and_tamper():
    s = _store()
    s.register("alice", "correct-horse-battery")
    tok = s.issue_token("alice", ttl=100, now=1000.0)
    assert s.verify_token(tok, now=1050.0) == "alice"
    assert s.verify_token(tok, now=2000.0) is None            # expired
    assert s.verify_token("not.a.token") is None
    assert s.verify_token(tok[:-3] + "xyz", now=1050.0) is None
    other = AuthStore(secret="a-completely-different-32char-secret!")
    other.register("alice", "correct-horse-battery")
    assert other.verify_token(tok, now=1050.0) is None        # wrong signing secret


def test_logout_revokes_all_outstanding_tokens():
    s = _store()
    s.register("erin", "passphrase-1234")
    tok = s.issue_token("erin", now=1000.0)
    assert s.verify_token(tok, now=1000.0) == "erin"
    s.revoke_sessions("erin")                                 # logout / password change
    assert s.verify_token(tok, now=1000.0) is None            # old token invalid
    assert s.verify_token(s.issue_token("erin", now=1000.0), now=1000.0) == "erin"  # fresh works


def test_deploy_guard_fails_closed_on_public():
    enforce_deploy_policy(env={})                             # not public -> no-op
    with pytest.raises(RuntimeError):
        enforce_deploy_policy(env={"OSAI_PUBLIC": "1"})       # public, auth off
    with pytest.raises(RuntimeError):
        enforce_deploy_policy(env={"OSAI_PUBLIC": "1", "OSAI_AUTH": "1", "OSAI_AUTH_SECRET": "short"})
    # public + auth + strong secret is allowed
    enforce_deploy_policy(env={"OSAI_PUBLIC": "1", "OSAI_AUTH": "1", "OSAI_AUTH_SECRET": "x" * 40})
    # explicit demo escape hatch
    enforce_deploy_policy(env={"OSAI_PUBLIC": "1", "OSAI_ALLOW_INSECURE_PUBLIC_DEMO": "1"})


def test_auth_secret_resolves_from_file(tmp_path):
    # Docker-secret file convention: OSAI_AUTH_SECRET_FILE beats the inline env var,
    # and the deploy guard reads the file-provided secret too.
    secret_file = tmp_path / "osai_auth_secret"
    secret_file.write_text("﻿" + "f" * 40 + "\n", encoding="utf-8")  # BOM + trailing ws tolerated
    env = {"OSAI_AUTH_SECRET_FILE": str(secret_file), "OSAI_AUTH_SECRET": "inline-loser"}
    assert read_secret(env) == "f" * 40                       # file wins, stripped
    enforce_deploy_policy(env={"OSAI_PUBLIC": "1", "OSAI_AUTH": "1", **env})  # strong file secret -> ok
    # a missing/empty file falls back to the inline env var
    assert read_secret({"OSAI_AUTH_SECRET_FILE": str(tmp_path / "nope"),
                        "OSAI_AUTH_SECRET": "x" * 40}) == "x" * 40


def test_unknown_user_verifies_against_dummy_hash():
    # unknown-user auth still runs a hash verify (constant timing) and returns False
    s = _store()
    assert s.verify_password("ghost", "any-password-here") is False
    assert s.authenticate("ghost", "any-password-here") is False


def test_auth_enabled_env(monkeypatch):
    monkeypatch.delenv("OSAI_AUTH", raising=False)
    assert auth_enabled() is False
    monkeypatch.setenv("OSAI_AUTH", "1")
    assert auth_enabled() is True
