# API Key & Data-Handling Policy

> Scope: how OSAI Prep Studio handles the Anthropic API key and what learner data may
> (and may not) leave the box when the optional generative LLM layer is enabled. This
> is a **gate**, not a nicety: the live transcript-judging paths stay OFF until every
> control below is in place and verified.

## 1. Trust model in one line

The platform is **offline-first and deterministic by default**. The hosted Anthropic
API is an *optional upgrade* reserved for the **tutor / judge / attacker-LLM** roles —
never the vulnerable lab target. Two separate opt-in gates fence it off, and the
lower-risk path (tutor) is the only one wired today.

## 2. The key never appears anywhere but the runtime environment

Do **not** put the Anthropic key in any of: chat, a PR, an issue, a README, a `.env`
committed to git, a `Dockerfile` `ENV`, or any command line that echoes into shell
history / process lists / CI logs.

The clean pattern:

```
ANTHROPIC_API_KEY lives only in the runtime environment / secret store
        ↓
code reads os.environ["ANTHROPIC_API_KEY"]   (osai_spine/llm.py)
        ↓
CI and offline tests never need it
        ↓
live LLM paths activate only when OSAI_LLM=1
```

> ⚠️ **A shared "Environment variables" box is NOT a secret store.** Some cloud/CI
> environment configs (e.g. Claude Code on the web) expose a plaintext env-vars field
> that is *visible to anyone using the environment* — and its own UI warns "don't add
> secrets or credentials." Do **not** put `ANTHROPIC_API_KEY` there, nor hardcode it in
> the Setup script (which is stored with the environment too).

Delivery, in order of preference:

1. **(Recommended) Run the live LLM path where you control the runtime** — your laptop
   (`export ANTHROPIC_API_KEY=…`, or a git-ignored `.env`) or your own deploy host /
   container (a Docker secret or platform secret manager). The studio is **offline-first**:
   a shared cloud/CI environment does **not** need the key, so keep it offline there.
2. **Inside a cloud session, only via a real secret manager** — if the key must be
   present in a hosted session, have the Setup script fetch it at start from a proper
   secrets manager (Vault / cloud secret manager / Doppler / 1Password CLI), e.g.
   `export ANTHROPIC_API_KEY="$(vault kv get -field=key secret/anthropic)"`. Only a
   short-lived, least-privileged token to that manager lives in the environment — never
   the key itself — and never `echo` it (setup logs).
3. **GitHub Actions (only if live-LLM CI is truly needed)** — a repository/environment
   **secret** named `ANTHROPIC_API_KEY`, referenced as an env var in the workflow (not
   on the command line). CI is green **without** it by design, so this is rarely needed.
4. **Docker / lab host** — a **secret file** or secret manager mounted at runtime (e.g.
   Docker secrets under `/run/secrets/…`), never an image layer or source file.

The operator verifies *presence only* (§5), never the value.

Repo guards already in place:

- `.gitignore` excludes `.env`, `.env.*`, `secrets/`, `config/credentials.json`,
  `*.key`, `*.pem`.
- `.claude/settings.json` **denies** reads of those same paths so the agent can't open
  a secret file even by accident.

## 3. Two-tier activation gates

| Gate | Env | Governs | Status |
|---|---|---|---|
| Base (tutor) | `OSAI_LLM=1` | query + **public reference corpus** only | wired; low risk |
| Transcripts | `OSAI_LLM=1` **and** `OSAI_LLM_TRANSCRIPTS=1` | report-judge / attacker-LLM that send **learner attack transcripts** | **HELD — not wired** |

`llm.enabled()` governs the first; `llm.transcripts_enabled()` requires the second,
explicit opt-in on top. With no key, no SDK, or no opt-in, every path degrades to the
deterministic offline behavior (extractive tutor, mock targets).

## 4. Data-handling controls for the transcript paths (the HOLD list)

The transcript-judging paths remain OFF until **all** of these hold:

- [x] **Runtime-env key only** — never in chat/git/images (§2).
- [x] **CI offline by default** — suite is green without the key; live-LLM tests are
      opt-in behind `OSAI_LLM=1` and skipped when the key is absent.
- [x] **Visible toggle** — `OSAI_LLM=1`, plus the separate `OSAI_LLM_TRANSCRIPTS=1`.
- [x] **Fake secrets only** — the range plants only non-production fake secrets/PII; no
      real data is ever in scope.
- [x] **Redaction before egress** — `llm.redact_transcript()` scrubs flags (`OSAI{…}`),
      emails, AWS keys, `sk-…` API keys, private-key blocks, and card-number runs from
      any transcript before an API call. Defense in depth on top of "fake secrets only."
- [ ] **No real learner PII in API calls** — enforced operationally: learner identifiers
      passed to the API are pseudonymous ids, not names/emails.
- [ ] **Transcript retention policy** — define request/response retention + deletion for
      the chosen Anthropic data path before enabling.
- [ ] **Spend cap** — a per-key / per-environment budget cap and alerting.
- [ ] **Log redaction** — application logs never record the key or un-redacted content.
- [ ] **Key rotation + revocation procedure** — documented owner, cadence, and the steps
      to revoke a leaked key.

Checked boxes are implemented in this repo; unchecked boxes are operational controls the
deployer must complete **before** flipping `OSAI_LLM_TRANSCRIPTS=1`.

## 4a. Setup steps (getting from zero to a working key)

1. **Create the key** — console.anthropic.com → API Keys → Create Key (`sk-ant-…`).
   Billed to your Anthropic API account (separate from any Claude.ai subscription).
2. **Place it** in a real secret location for wherever the code runs (§2): a shell
   `export`, a git-ignored `.env`, a Docker secret, or a secret manager the Setup
   script reads at start. **Not** a shared "Environment variables" box (plaintext) and
   **not** hardcoded in a Setup script.
3. **Base-URL gotcha** — some hosts (e.g. a Claude Code session) set
   `ANTHROPIC_BASE_URL` to an *agent* proxy. So the app doesn't inherit that, set
   `OSAI_ANTHROPIC_BASE_URL=https://api.anthropic.com` for the app (the provider
   passes it explicitly), or run the app on a host where `ANTHROPIC_BASE_URL` isn't
   the agent proxy. With neither set, the SDK's default endpoint is used.
4. **Enable + verify** — `export OSAI_LLM=1` then `python -m osai_spine.cli llm`
   (§5). `GET /health` then shows `"llm": {"enabled": true}` and tutor answers are
   tagged `[AI · grounded]`.

## 5. Safe verification (presence, not value)

The only sanctioned check prints **yes/no** — never the value, prefix, suffix, length,
or a hash:

```bash
python -m osai_spine.cli llm
# ANTHROPIC_API_KEY present: yes/no
# anthropic SDK installed:   yes/no
# OSAI_LLM (tutor) enabled:  yes/no
# OSAI_LLM_TRANSCRIPTS gate: yes/no
# model (quality / bulk):    claude-opus-4-8 / claude-haiku-4-5
```

`GET /health` exposes the same booleans (`status()`), and `status()` is unit-tested to
never echo the key value.

## 6. Blast radius

If the key leaks: revoke it immediately at the Anthropic console, rotate, and audit
spend. Because the key is environment-only and never in git, a repo leak cannot expose
it; because lab containers are egress-deny (13-platform-threat-model.md), a compromised
lab cannot exfiltrate it either.

## Cross-references
[../../07-architecture-and-stack.md](../../07-architecture-and-stack.md) ·
[../../11-safety-legal-ethics.md](../../11-safety-legal-ethics.md) ·
[../../13-platform-threat-model.md](../../13-platform-threat-model.md) ·
[../../04-evaluation-harness.md](../../04-evaluation-harness.md)
