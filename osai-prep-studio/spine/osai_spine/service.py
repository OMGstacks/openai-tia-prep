"""A minimal HTTP grader service (stdlib ``http.server``).

Exposes the grading slice of the API surface in 07-architecture-and-stack.md with
zero new runtime dependencies, so it runs and is testable anywhere (the production
target is FastAPI; the contract is the same). Learner-facing responses are
**answer-redacted**: public lab views omit the grading internals, and submit
responses use ``GradeResult.public_feedback()`` (no expected detector / OWASP id).

Endpoints:
    GET  /health
    GET  /catalog
    GET  /labs
    GET  /labs/{id}            (public, redacted manifest)
    POST /labs/{id}/submit     {learner_id, transcript, flag, attempt?}
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import engine
from . import manifest as manifest_mod
from .taxonomy import TaxonomyRegistry
from .validator import ChallengeValidator

# Fields that would leak the answer key — never sent to learners.
_REDACTED = {"two_signal_grading", "reuse_asset", "hint_ladder", "attack_graph"}

_LABS_DIR = Path(__file__).resolve().parent.parent / "labs"


def _public_manifest(manifest: dict) -> dict:
    return {k: v for k, v in manifest.items() if k not in _REDACTED}


class GraderState:
    def __init__(self, seed: str, labs_dir):
        self.seed = seed
        self.labs_dir = Path(labs_dir)
        self.registry = TaxonomyRegistry()
        self.labs = {p.stem: manifest_mod.load(p) for p in sorted(self.labs_dir.glob("*.json"))}


def _make_handler(state: GraderState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the test/CI output quiet
            return

        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"status": "ok", "engine": engine.ENGINE_PATH})
            if self.path == "/catalog":
                r = state.registry
                return self._send(200, {
                    "detectors": r.detector_names(),
                    "owasp_llm_2025": r.owasp,
                    "owasp_agentic": r.agentic,
                })
            if self.path == "/labs":
                return self._send(200, [
                    {"id": m["id"], "title": m["title"], "difficulty": m.get("difficulty")}
                    for m in state.labs.values()
                ])
            if self.path.startswith("/labs/"):
                lab_id = self.path[len("/labs/"):].strip("/")
                m = state.labs.get(lab_id)
                if not m:
                    return self._send(404, {"error": "no such lab"})
                return self._send(200, _public_manifest(m))
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": "invalid JSON"})

            if self.path.startswith("/labs/") and self.path.endswith("/submit"):
                lab_id = self.path[len("/labs/"):-len("/submit")].strip("/")
                m = state.labs.get(lab_id)
                if not m:
                    return self._send(404, {"error": "no such lab"})
                learner = payload.get("learner_id")
                if not learner:
                    return self._send(400, {"error": "learner_id required"})
                result = ChallengeValidator(m).grade(
                    payload.get("transcript", []),
                    payload.get("flag", ""),
                    state.seed,
                    learner,
                    int(payload.get("attempt", 0)),
                )
                return self._send(200, result.public_feedback())
            return self._send(404, {"error": "not found"})

    return Handler


def build_server(host: str = "127.0.0.1", port: int = 0, seed: str | None = None, labs_dir=None):
    """Build (but do not start) the grader server. Returns (server, state)."""
    seed = seed or os.environ.get("OSAI_SERVER_SEED", "dev-seed-change-me")
    state = GraderState(seed, labs_dir or _LABS_DIR)
    server = ThreadingHTTPServer((host, port), _make_handler(state))
    return server, state
