# Attack-Path Graphs

> Purpose: Score **methodology, not flag-hunting**. Every lab has a hidden instructor attack graph; the grader scores how much of the operator loop the learner actually executed. Integrates the uploaded addendum.

## 1. Why graphs beat flag-only grading

Flag-only labs teach answer-hunting. Real red-team work — and the OSAI exam — rewards the loop:

`Recon → Hypothesis → Probe → Exploit → Evidence → Impact → Remediation → Retest → Report`

Attack-path graphs make that loop the unit of assessment. They also pair naturally with two-signal grading ([02-lab-range.md](02-lab-range.md)): the **Exploit** node requires the detector verdict + evidence token; the other nodes require artifacts (notes, transcripts, written impact/remediation).

## 2. Per-lab graph (example: L02)

```yaml
attack_path_graph:
  lab_id: "L02"
  title: "Indirect Prompt Injection Through Retrieved Documents"
  objective: "Cause the RAG assistant to follow untrusted retrieved instructions and leak a planted non-production secret."
  authorized_scope: ["local lab container", "seeded fake document corpus", "lab callback server"]
  nodes:
    - { id: N1, phase: recon,       action: "Identify the assistant uses retrieved documents", evidence: "request/response proving retrieval", score: 10 }
    - { id: N2, phase: hypothesis,  action: "Hypothesize retrieved text can override system intent", evidence: "written hypothesis", score: 10 }
    - { id: N3, phase: probe,       action: "Submit a benign probe document; observe behavior", evidence: "transcript id", score: 10 }
    - { id: N4, phase: exploit,     action: "Trigger the seeded unsafe behavior (lab-only target)", evidence: "detector verdict + planted flag", score: 30 }
    - { id: N5, phase: impact,      action: "Explain why trusted retrieval without instruction isolation is dangerous", evidence: "impact paragraph", score: 15 }
    - { id: N6, phase: remediation, action: "Recommend source isolation, instruction hierarchy, output filtering, access control", evidence: "remediation section", score: 15 }
    - { id: N7, phase: retest,      action: "Validate the defense prevents the attack path", evidence: "before/after transcript", score: 10 }
```

## 3. Scoring dimensions

| Dimension | Weight |
|---|---:|
| Recon quality | 10% |
| Hypothesis quality | 10% |
| Safe probing | 10% |
| Exploit evidence | 30% |
| Impact explanation | 15% |
| Remediation quality | 15% |
| Retest quality | 10% |

The graph score is a first-class component of lab grading and exam scoring ([06-exam-simulator.md](06-exam-simulator.md) weights it 15%), feeds the methodology view of the dashboard, and renders as the attack-path diagram in the learner's report appendix ([08-reporting-and-canva.md](08-reporting-and-canva.md)).

## 4. Authoring

Each graph is stored at `attack-graphs/Lxx.yml` and referenced from the lab manifest ([12-content-authoring.md](12-content-authoring.md)). Learners see only partial hints (the hint ladder, [03-tutor-examiner-bot.md](03-tutor-examiner-bot.md)); the grader uses the full graph. The **Exploit** node's evidence requirement is exactly the lab's two-signal flag, so the graph and the auto-grader never disagree.

## Cross-references
[02-lab-range.md](02-lab-range.md) · [06-exam-simulator.md](06-exam-simulator.md) · [08-reporting-and-canva.md](08-reporting-and-canva.md) · [12-content-authoring.md](12-content-authoring.md)
