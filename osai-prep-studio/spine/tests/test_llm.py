"""The optional LLM provider seam + the tutor's generative path.

No live API call: a fake provider drives the seam so the grounding gate, the
extractive fallback, and the taxonomy guard are all verified offline. The default
(no provider) path stays byte-for-byte the extractive behavior."""

import os
import time

import pytest

from osai_spine import llm as llm_mod
from osai_spine.taxonomy import TaxonomyRegistry
from osai_spine.tutor import Tutor


class _FakeProvider:
    """Stands in for LLMProvider — records the call and returns a canned answer."""

    def __init__(self, reply=None, raises=False):
        self.reply, self.raises, self.calls = reply, raises, []

    def complete(self, system, user, *, model=None, max_tokens=700, cached_prefix=None):
        self.calls.append({"system": system, "user": user, "cached_prefix": cached_prefix})
        if self.raises:
            raise RuntimeError("simulated API error")
        return self.reply


def test_enabled_is_off_without_optin(monkeypatch):
    # No SDK is installed in CI, so the seam must report disabled regardless of flags.
    monkeypatch.setenv("OSAI_LLM", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    # enabled() also requires the SDK; absent here -> False, never touching the network
    assert llm_mod.enabled() is (llm_mod.sdk_available() and True)
    st = llm_mod.status()
    assert st["model_quality"] == "claude-opus-4-8"
    assert set(st) >= {"enabled", "sdk_installed", "key_present", "model_quality", "model_bulk"}


def test_default_tutor_is_extractive():
    t = Tutor(registry=TaxonomyRegistry())  # no llm
    r = t.ask("what is prompt injection")
    assert r["abstained"] is False
    assert r["generative"] is False
    assert r["citations"]


def test_generative_answer_used_when_grounded():
    fake = _FakeProvider(reply="Prompt injection (LLM01:2025) overrides instructions. [1]")
    t = Tutor(registry=TaxonomyRegistry(), llm=fake)
    r = t.ask("what is prompt injection")
    assert r["generative"] is True
    assert r["answer"].startswith("Prompt injection")
    assert r["taxonomy_ids_valid"] is True
    # the seam was handed the retrieved corpus as a cacheable prefix
    assert fake.calls and fake.calls[0]["cached_prefix"].startswith("SOURCES:")


def test_hallucinated_id_falls_back_to_extractive():
    fake = _FakeProvider(reply="See LLM77:2025, a made-up category.")  # not a real id
    t = Tutor(registry=TaxonomyRegistry(), llm=fake)
    r = t.ask("what is prompt injection")
    assert r["generative"] is False          # rejected -> extractive fallback
    assert "LLM77:2025" not in r["answer"]
    assert r["taxonomy_ids_valid"] is True


def test_provider_error_falls_back_to_extractive():
    t = Tutor(registry=TaxonomyRegistry(), llm=_FakeProvider(raises=True))
    r = t.ask("what is prompt injection")
    assert r["generative"] is False
    assert r["citations"]


def test_status_never_leaks_the_key_value(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret-value-should-never-appear")
    st = llm_mod.status()
    blob = repr(st)
    assert "sk-secret-value-should-never-appear" not in blob
    assert st["key_present"] is True            # presence only
    assert "transcripts_enabled" in st


def test_key_from_docker_secret_file(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    secret = tmp_path / "anthropic_api_key"
    secret.write_text("sk-ant-from-file\n")  # trailing newline is stripped
    monkeypatch.setenv("ANTHROPIC_API_KEY_FILE", str(secret))
    assert llm_mod.key_present() is True
    assert llm_mod.key_source() == "file"
    assert llm_mod._read_key() == "sk-ant-from-file"
    assert llm_mod.status()["key_source"] == "file"
    # a direct env var wins over the file
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")
    assert llm_mod.key_source() == "env" and llm_mod._read_key() == "sk-ant-from-env"


def test_key_file_with_bom_is_cleaned(tmp_path, monkeypatch):
    # A Windows-written secret file may carry a UTF-8 BOM; it must not corrupt the key.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    secret = tmp_path / "anthropic_api_key"
    secret.write_bytes(b"\xef\xbb\xbfsk-ant-bom\r\n")  # BOM + CRLF
    monkeypatch.setenv("ANTHROPIC_API_KEY_FILE", str(secret))
    assert llm_mod._read_key() == "sk-ant-bom"


def test_missing_secret_file_is_safe(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY_FILE", "/no/such/secret")
    assert llm_mod.key_present() is False and llm_mod.key_source() == "none"


def test_base_url_override_from_env(monkeypatch):
    monkeypatch.setenv("OSAI_ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    p = llm_mod.LLMProvider()
    assert p.base_url == "https://api.anthropic.com"
    assert llm_mod.status()["base_url_override"] is True
    monkeypatch.delenv("OSAI_ANTHROPIC_BASE_URL", raising=False)
    assert llm_mod.LLMProvider().base_url is None


def test_transcripts_gate_is_second_optin(monkeypatch):
    # Even with the base tutor gate on, transcript paths stay OFF without the second
    # explicit opt-in — the learner-content HOLD enforced in code.
    monkeypatch.setenv("OSAI_LLM", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OSAI_LLM_TRANSCRIPTS", raising=False)
    assert llm_mod.transcripts_enabled() is False


def test_redaction_scrubs_flags_secrets_and_pii():
    raw = ("user alice@example.com leaked OSAI{abc123} and AKIA0123456789ABCDEF "
           "plus sk-abcdefgh12345678ijkl and card 4111 1111 1111 1111")
    red = llm_mod.redact_text(raw)
    assert "OSAI{abc123}" not in red and "[REDACTED_FLAG]" in red
    assert "alice@example.com" not in red and "[REDACTED_EMAIL]" in red
    assert "AKIA0123456789ABCDEF" not in red and "[REDACTED_AWS_KEY]" in red
    assert "sk-abcdefgh12345678ijkl" not in red and "[REDACTED_API_KEY]" in red
    assert "4111 1111 1111 1111" not in red


def test_redact_transcript_preserves_shape():
    tr = [{"role": "user", "source": "chat_ui", "content": "the flag is OSAI{x}"}]
    red = llm_mod.redact_transcript(tr)
    assert red[0]["role"] == "user" and red[0]["source"] == "chat_ui"
    assert "OSAI{x}" not in red[0]["content"]
    assert tr[0]["content"] == "the flag is OSAI{x}"  # original untouched (copy)


def test_rate_limiter_caps_and_slides():
    rl = llm_mod._RateLimiter(max_calls=3, window_s=60.0)
    assert rl.allow(0.0) and rl.allow(1.0) and rl.allow(2.0)  # 3 allowed in-window
    assert rl.allow(3.0) is False                             # 4th blocked
    assert rl.allow(61.0) is True                             # earliest slid out of window
    disabled = llm_mod._RateLimiter(0)                        # 0 => no cap
    assert all(disabled.allow(float(i)) for i in range(100))


def test_provider_rate_limit_raises_before_touching_client():
    p = llm_mod.LLMProvider(max_calls_per_min=1)
    assert p._limiter.allow(time.monotonic())  # consume the only slot
    # the next completion trips the cap BEFORE importing/using the SDK client
    with pytest.raises(llm_mod.LLMRateLimited):
        p.complete("system", "user")


def test_status_reports_call_cap():
    assert "max_calls_per_min" in llm_mod.status()


def test_cli_llm_ping_skips_when_disabled(monkeypatch, capsys):
    from osai_spine.cli import main

    monkeypatch.delenv("OSAI_LLM", raising=False)  # not enabled -> ping is skipped, not attempted
    rc = main(["llm", "--ping"])
    assert rc == 1
    assert "ping: skipped" in capsys.readouterr().out


def test_abstention_unaffected_by_provider():
    # An off-corpus query must still abstain — the LLM is never consulted.
    fake = _FakeProvider(reply="(should never be used)")
    t = Tutor(registry=TaxonomyRegistry(), llm=fake)
    r = t.ask("sourdough bread recipe at altitude")
    assert r["abstained"] is True
    assert fake.calls == []
