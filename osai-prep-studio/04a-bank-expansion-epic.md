# Bank Expansion Epic — reaching ~750 the right way

> Companion to [04-evaluation-harness.md](04-evaluation-harness.md). This epic tracks the
> build-out of the gold set from the **v0.3 milestone (280 items, 4 banks)** to the
> **~750-item, 9-bank** target — through **new grader-backed bank types**, not padding.

## Context

The gold set reached 280 quality-vetted items across four banks (framework_recall,
abstention, refusal, lab_answer_leakage). Those four are **structurally capped**:
`framework_recall` is bounded by corpus coverage, and the other three degrade into
near-duplicates past their design size. Padding them to 750 would make the dashboard bigger
while making the ship gate **weaker** — a padded compliance artifact.

The remaining ~470 items must therefore come from the **five unbuilt doc-04 bank types**,
each of which tests a genuinely different capability and needs **its own grader**. The rule
for this epic: **graders first, items second**, and every item carries a `bank`, `source`,
grader, expected behaviour, and failure mode.

## Non-negotiable process (per bank)

1. **Define the rubric** — what the bank tests and the exact pass condition.
2. **Implement the grader** in `goldset.py` and add it to the `GATE` (its pass-rate is
   hard-gated, so any item the grader fails blocks CI).
3. **Add a small seed set** (10–20 items) via generate-and-filter against the real tutor +
   the new grader.
4. **Prove the grader fails bad answers** — a unit test where a wrong / abstained /
   invented / hallucinated answer is graded `False`.
5. **Generate in batches of 25–50**, running the ship gate and **deduping (by id AND
   prompt)** after every batch.

No bulk generation without dedupe; no target-count padding; no bank without a grader.

## Sequence (by dependency + grading complexity)

| Phase | Bank(s) | Grader idea | Status |
|---|---|---|---|
| **1** | `architecture_reasoning`, `lab_grounded` | Grounded + cited + **required fact present** + **no invention** (anti-fabrication), over a new `reference/osai-studio-architecture.md` corpus doc | **✅ landed** — graders + gate + 28 vetted seeds (15 + 13) + grader-teeth test |
| **2** | `tool_use_judgment` | Grade the **decision** (allow / block / require-approval; injection-vs-benign) against an expected label — not just the explanation | ⬜ next |
| **3** | `stale_claim_detection` | Given a claim, the tutor must **flag it stale**, name the fresher source, and answer/abstain/caveat correctly | ⬜ |
| **4** | `report_quality` | Reuse the existing `ReportReviewer` rubric — item = finding + expected rubric outcome; assert score/pass matches | ⬜ |

## Target distribution (~750; ranges, not exact equality)

| Bank | Target |
|---|---:|
| framework_recall | 140–160 |
| abstention | 75–100 |
| refusal | 75–100 |
| lab_answer_leakage | 75–100 |
| architecture_reasoning | 75–100 |
| lab_grounded | 125–150 |
| report_quality | 100–125 |
| stale_claim_detection | 50–75 |
| tool_use_judgment | 50–75 |
| **Total** | **~750** |

## Acceptance criteria for "750 achieved"

- Every bank has a **grader** and is **hard-gated** (no ungated bank).
- No item without **provenance** (`bank`, `source`) or **expected behaviour**.
- **0** hallucinated taxonomy ids; **0** lab-answer-leakage failures.
- No **near-duplicate padding** (dedupe by id + prompt enforced each batch).
- Old **abstention/refusal** behaviour still passes (no regression).
- All **CI and ship gates green**, and every bank passes **independently**.
- The gate report includes per-bank: `item_count`, `source_corpus`, `grader_name`,
  `pass_rate`, and failure examples.

## Phase 1 result (this epic's first delivery)

- New corpus doc `reference/osai-studio-architecture.md` (component ownership, trust
  boundaries, two-signal + Signal C grading, per-lab attack→detector→defense), wired into
  `tutor.DEFAULT_SOURCES`.
- `goldset.py` grades `architecture_reasoning` + `lab_grounded` as grounded-and-cited with
  a **required-keyword / anti-invention** check; both hard-gated at pass-rate 1.0.
- 28 vetted seeds; a unit test proves the grader **fails** missing-fact, abstained,
  uncited, invented, and hallucinated answers. Gold set now **308 items**, ship gate PASS.
