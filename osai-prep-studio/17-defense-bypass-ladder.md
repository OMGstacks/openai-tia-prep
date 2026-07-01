# Defense Bypass Ladder

> Purpose: Teach how attacks change as **defenses mature**, not just how to break naked toy systems. Each high-value vulnerability ships in multiple defense-maturity variants. Integrates the uploaded addendum.

## 1. Why

A world-class operator knows that "it worked on the D0 lab" is not a finding against a hardened enterprise. The ladder builds the instinct to *escalate technique as controls improve* — and gives defenders a realistic sense of residual risk. It maps directly onto the exam's enterprise targets, which sit at varying maturity.

## 2. Defense maturity ladder

| Level | Name | Target properties | Learner objective |
|---|---|---|---|
| `D0` | Naked Target | No meaningful controls | Learn the basic vulnerability |
| `D1` | System Prompt Only | Defensive instruction in the system prompt | Show why prompt-only defense fails |
| `D2` | Keyword Filter | Naive denylist/regex | Demonstrate evasion + false positives |
| `D3` | Output Sanitizer | Post-generation filtering | Show downstream-trust/context failures |
| `D4` | Retrieval Filter | Basic RAG source filtering | Test metadata, chunking, source trust, access control |
| `D5` | Tool Permission Check | Tool allowlist + basic authz | Test excessive agency / confused deputy |
| `D6` | Human-in-the-Loop | Approval required for risky action | Test approval-text quality + hidden-instruction propagation |
| `D7` | Policy Engine + Audit | Scoped tokens, policy engine, audit logs, rate limits | Test multi-step abuse, monitoring, alert quality |
| `D8` | Mature Enterprise Control Plane | Identity, logging, least privilege, sandboxing, evals, IR | Produce a professional report with realistic residual risk |

## 3. Lab requirement

Each high-value vulnerability ships **≥3 variants**, e.g.:

```yaml
defense_variants: [D0_basic_vulnerable, D3_output_sanitized, D7_policy_audited]
```

The variant is a field on the lab manifest ([12-content-authoring.md](12-content-authoring.md)); the `defense_level` also informs the attack-path graph's expected technique sophistication.

## 4. Minimum required coverage

| Vulnerability family | Required defense levels |
|---|---|
| Prompt injection (L01/L03) | D0, D1, D2, D7 |
| Indirect injection / RAG (L02) | D0, D4, D7 |
| System-prompt leakage (L04) | D0, D2, D7 |
| Excessive agency / tool misuse (L16) | D0, D5, D6, D7 |
| MCP / tool shadowing (L11/L12) | D0, D5, D7 |
| Memory poisoning (L15) | D0, D4, D7 |
| Unbounded consumption (L19) | D0, D2, D7 |
| Supply chain (L17) | D0, D7, D8 |

The defender's perspective at each rung also seeds the **blue-team labs** ([02-lab-range.md](02-lab-range.md) L20) and the remediation sections of reports ([19-business-impact-rubric.md](19-business-impact-rubric.md)).

## Cross-references
[02-lab-range.md](02-lab-range.md) · [12-content-authoring.md](12-content-authoring.md) · [16-attack-path-graphs.md](16-attack-path-graphs.md) · [19-business-impact-rubric.md](19-business-impact-rubric.md)
