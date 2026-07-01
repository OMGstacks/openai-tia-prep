"""Append-only security audit log (stdlib SQLite).

Records who did what, when — auth events (register/login/logout/failure) and
security-relevant actions (lab submissions and their grade decision). Never stores
secrets, passwords, tokens, flags, or answer keys — only actor + event + a small
non-sensitive detail. Reads are for an instructor/admin view and tests.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time

# Recognized event names (free-form is allowed, but these are the wired ones).
AUTH_REGISTER = "auth.register"
AUTH_LOGIN = "auth.login"
AUTH_LOGIN_FAILURE = "auth.login_failure"
AUTH_LOGIN_THROTTLED = "auth.login_throttled"
AUTH_LOGOUT = "auth.logout"
LAB_SUBMIT = "lab.submit"


class AuditLog:
    def __init__(self, db_path: str = ":memory:"):
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS audit ("
                "  id     INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  ts     REAL NOT NULL,"
                "  event  TEXT NOT NULL,"
                "  actor  TEXT,"
                "  detail TEXT)"
            )
            self.conn.commit()

    def record(self, event: str, actor: str | None = None, detail: dict | None = None,
               now: float | None = None) -> None:
        now = float(now) if now is not None else time.time()
        with self._lock:
            self.conn.execute(
                "INSERT INTO audit(ts,event,actor,detail) VALUES(?,?,?,?)",
                (now, event, actor, json.dumps(detail or {}, separators=(",", ":"))),
            )
            self.conn.commit()

    def recent(self, limit: int = 50, actor: str | None = None) -> list:
        if actor is not None:
            rows = self.conn.execute(
                "SELECT ts,event,actor,detail FROM audit WHERE actor=? ORDER BY id DESC LIMIT ?",
                (actor, int(limit)),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT ts,event,actor,detail FROM audit ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [
            {"ts": r["ts"], "event": r["event"], "actor": r["actor"],
             "detail": json.loads(r["detail"] or "{}")}
            for r in rows
        ]
