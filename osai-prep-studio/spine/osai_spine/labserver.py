"""Lab-target server — the deliberately-vulnerable target a learner attacks.

Containerized as the lab-target image. Plants a per-learner flag derived from the
shared seed (so the grader verifies it without the two services exchanging the flag)
and exposes the target over HTTP. Stdlib-only.

    POST /chat   {"message": "..."}   -> {"response": "...", ...}
    GET  /health

Env: OSAI_SERVER_SEED, OSAI_LEARNER (default 'demo-learner'), OSAI_LAB (default 'L01'),
     OSAI_HOST (default 0.0.0.0), OSAI_PORT (default 9001).
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import flags
from .labtarget import MockMcpTarget, MockRagTarget, make_chat_target


def _build_target(lab_id: str, flag: str):
    if lab_id == "L02":
        return "rag", MockRagTarget(flag)
    if lab_id == "L11":
        return "mcp", MockMcpTarget(flag)
    # chat labs: the deterministic mock by default, or an Ollama-backed model when
    # OSAI_OLLAMA=1 (the deploy-time realism upgrade) — same contract either way.
    return "chat", make_chat_target(flag)


def _make_handler(kind, target):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
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
                return self._send(200, {"status": "ok", "kind": kind})
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": "invalid JSON"})
            if self.path != "/chat":
                return self._send(404, {"error": "not found"})
            message = payload.get("message", "")
            if kind == "rag":
                target.ingest(message)  # the learner injects a document
                retrieved, answer = target.query("(benign retrieval query)")
                return self._send(200, {"response": answer, "retrieved": retrieved, "tool": None})
            if kind == "mcp":
                answer, tool = target.chat(message)
                return self._send(200, {"response": answer, "tool": tool})
            return self._send(200, {"response": target.chat(message), "tool": None})

    return Handler


def main():
    seed = os.environ.get("OSAI_SERVER_SEED", "dev-seed-change-me")
    learner = os.environ.get("OSAI_LEARNER", "demo-learner")
    lab = os.environ.get("OSAI_LAB", "L01")
    host = os.environ.get("OSAI_HOST", "0.0.0.0")
    port = int(os.environ.get("OSAI_PORT", "9001"))

    flag = flags.derive_flag(seed, learner, lab)
    kind, target = _build_target(lab, flag)
    server = ThreadingHTTPServer((host, port), _make_handler(kind, target))
    print(f"lab-target {lab} ({kind}) on http://{host}:{port} learner={learner}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
