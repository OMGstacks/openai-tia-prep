"""osai_spine CLI — the spine's runnable surface.

    python -m osai_spine.cli catalog
    python -m osai_spine.cli validate-manifests
    python -m osai_spine.cli derive-flag --seed S --learner alice --lab L01
    python -m osai_spine.cli grade --lab L01 --transcript t.json \
        --flag 'OSAI{...}' --seed S --learner alice
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import engine, flags
from . import manifest as manifest_mod
from .taxonomy import TaxonomyRegistry
from .validator import ChallengeValidator

LABS_DIR = Path(__file__).resolve().parents[1] / "labs"


def cmd_catalog(args) -> int:
    reg = TaxonomyRegistry()
    print(json.dumps(
        {
            "engine": engine.ENGINE_PATH,
            "detectors": reg.detector_names(),
            "owasp_llm_2025": reg.owasp,
            "owasp_agentic_T1_T15": reg.agentic,
        },
        indent=2,
    ))
    return 0


def cmd_validate(args) -> int:
    reg = TaxonomyRegistry()
    report = manifest_mod.validate_dir(args.labs or LABS_DIR, reg)
    ok = True
    if not report:
        print(f"(no manifests found in {args.labs or LABS_DIR})")
    for name, errs in report.items():
        if errs:
            ok = False
            print(f"FAIL {name}")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"OK   {name}")
    return 0 if ok else 1


def cmd_flag(args) -> int:
    print(flags.derive_flag(args.seed, args.learner, args.lab, args.attempt))
    return 0


def cmd_tutor(args) -> int:
    from . import llm as llm_mod
    from .tutor import Tutor

    # Wire the generative provider when the key is live (else offline extractive).
    provider = llm_mod.LLMProvider() if llm_mod.enabled() else None
    tutor = Tutor(registry=TaxonomyRegistry(), llm=provider)
    print(json.dumps(tutor.ask(args.query, args.mode), indent=2))
    return 0


def cmd_llm(args) -> int:
    """Safe presence check — prints only yes/no, NEVER the key value, prefix, suffix,
    length, or hash (docs/security/api-key-and-data-handling.md)."""
    from . import llm as llm_mod

    yn = lambda b: "yes" if b else "no"  # noqa: E731
    print(f"ANTHROPIC_API_KEY present: {yn(llm_mod.key_present())} (source: {llm_mod.key_source()})")
    print(f"anthropic SDK installed:   {yn(llm_mod.sdk_available())}")
    print(f"OSAI_LLM (tutor) enabled:  {yn(llm_mod.enabled())}")
    print(f"OSAI_LLM_TRANSCRIPTS gate: {yn(llm_mod.transcripts_enabled())}")
    print(f"model (quality / bulk):    {llm_mod.MODEL_QUALITY} / {llm_mod.MODEL_BULK}")
    if getattr(args, "ping", False):
        if not llm_mod.enabled():
            print("ping: skipped — need ANTHROPIC_API_KEY (or _FILE) + the anthropic SDK + OSAI_LLM=1")
            return 1
        try:
            out = llm_mod.LLMProvider().complete(
                "You are a connectivity check. Reply with exactly: OK", "ping", max_tokens=16)
            print(f"ping: live model replied -> {out!r}")
            return 0
        except Exception as exc:  # surface the real reason (401, bad base_url, network…)
            print(f"ping: FAILED -> {type(exc).__name__}: {exc}")
            return 1
    return 0


def cmd_goldset(args) -> int:
    from .goldset import GoldSetRunner, load_goldset

    gs = load_goldset(args.goldset) if args.goldset else None
    report = GoldSetRunner().run(gs)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"gold set: {report['total']} items {report['by_bank']}")
        for k, v in report["metrics"].items():
            print(f"  {'OK ' if report['gate'][k] else 'XXX'} {k}: {v}")
        for k, v in report["soft_metrics"].items():
            print(f"  ··· {k}: {v}  (tracked, not gated)")
        if report["failures"]:
            print("failures:", ", ".join(f"{f['id']}({f['bank']})" for f in report["failures"]))
        print("SHIP GATE:", "PASS" if report["passed"] else "FAIL")
    return 0 if report["passed"] else 1


def cmd_capstone(args) -> int:
    from .capstone import TriageCapstone

    cap = TriageCapstone()
    if args.brief:
        print(json.dumps(cap.public_brief(), indent=2))
        return 0
    if not args.submission:
        print("provide --submission <findings.json> or --brief")
        return 2
    submission = json.loads(Path(args.submission).read_text(encoding="utf-8"))
    result = cap.score(submission)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 2


def cmd_report(args) -> int:
    from .report import ReportReviewer

    finding = json.loads(Path(args.finding).read_text(encoding="utf-8"))
    transcript = json.loads(Path(args.transcript).read_text(encoding="utf-8")) if args.transcript else None
    card = ReportReviewer(TaxonomyRegistry()).review(finding, transcript)
    print(json.dumps(card.to_dict(), indent=2))
    return 0 if card.passed else 2


def cmd_serve(args) -> int:
    from .service import build_server

    server, state = build_server(host=args.host, port=args.port, seed=args.seed)
    host, port = server.server_address
    print(f"OSAI spine grader on http://{host}:{port}  (labs: {sorted(state.labs)})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        server.shutdown()
    return 0


def cmd_grade(args) -> int:
    path = Path(args.manifest) if args.manifest else (args.labs or LABS_DIR) / f"{args.lab}.json"
    manifest = manifest_mod.load(path)
    transcript = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    result = ChallengeValidator(manifest).grade(
        transcript, args.flag, args.seed, args.learner, args.attempt
    )
    if getattr(args, "db", None):
        from .progress import ProgressStore

        ProgressStore(args.db).record_attempt(args.learner, manifest, result)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 2


def cmd_progress(args) -> int:
    from .progress import ProgressStore

    store = ProgressStore(args.db)
    print(json.dumps(store.summary(args.learner, TaxonomyRegistry()), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="osai_spine")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("catalog", help="print the canonical taxonomy registry")
    sp.set_defaults(fn=cmd_catalog)

    sp = sub.add_parser("validate-manifests", help="validate lab manifests (the binding rule)")
    sp.add_argument("--labs", type=Path)
    sp.set_defaults(fn=cmd_validate)

    sp = sub.add_parser("derive-flag", help="derive a per-learner evidence flag")
    sp.add_argument("--seed", required=True)
    sp.add_argument("--learner", required=True)
    sp.add_argument("--lab", required=True)
    sp.add_argument("--attempt", type=int, default=0)
    sp.set_defaults(fn=cmd_flag)

    sp = sub.add_parser("tutor", help="ask the retrieval-grounded tutor (offline, cited)")
    sp.add_argument("--query", required=True)
    sp.add_argument("--mode", default="tutor")
    sp.set_defaults(fn=cmd_tutor)

    sp = sub.add_parser("serve", help="run the HTTP grader service")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8077)
    sp.add_argument("--seed", default=None)
    sp.set_defaults(fn=cmd_serve)

    sp = sub.add_parser("grade", help="two-signal grade a learner submission")
    sp.add_argument("--lab", required=True)
    sp.add_argument("--transcript", required=True)
    sp.add_argument("--flag", required=True)
    sp.add_argument("--seed", required=True)
    sp.add_argument("--learner", required=True)
    sp.add_argument("--attempt", type=int, default=0)
    sp.add_argument("--labs", type=Path)
    sp.add_argument("--manifest", help="path to a manifest (overrides --lab/--labs)")
    sp.add_argument("--db", help="record the attempt to this SQLite progress DB")
    sp.set_defaults(fn=cmd_grade)

    sp = sub.add_parser("progress", help="show a learner's progress from a SQLite DB")
    sp.add_argument("--db", required=True)
    sp.add_argument("--learner", required=True)
    sp.set_defaults(fn=cmd_progress)

    sp = sub.add_parser("llm", help="safe LLM seam status (presence only — never the key value)")
    sp.add_argument("--ping", action="store_true",
                    help="send a tiny live request to verify the key answers (surfaces errors)")
    sp.set_defaults(fn=cmd_llm)

    sp = sub.add_parser("goldset", help="run the tutor gold-set ship gate (04-evaluation-harness.md)")
    sp.add_argument("--goldset", help="path to a gold-set JSON (defaults to gold/goldset.json)")
    sp.add_argument("--json", action="store_true", help="emit the full JSON report")
    sp.set_defaults(fn=cmd_goldset)

    sp = sub.add_parser("capstone", help="L20 blue-team triage capstone (score a triage vs engine ground truth)")
    sp.add_argument("--brief", action="store_true", help="print the incident log + task (no answer key)")
    sp.add_argument("--submission", help="path to a triage submission JSON")
    sp.set_defaults(fn=cmd_capstone)

    sp = sub.add_parser("report", help="grade a learner finding vs the business-impact rubric")
    sp.add_argument("--finding", required=True, help="path to a finding JSON")
    sp.add_argument("--transcript", help="path to the attack transcript JSON (for classification check)")
    sp.set_defaults(fn=cmd_report)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
