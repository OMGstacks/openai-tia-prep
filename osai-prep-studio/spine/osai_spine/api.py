"""Production FastAPI grader app — same contract as the stdlib ``service.py``.

    uvicorn osai_spine.api:app --host 0.0.0.0 --port 8077

Reuses ``GraderState`` / ``ChallengeValidator`` and the answer-redaction from
``service.py``; learner responses never include the expected detector/OWASP id
(13-platform-threat-model.md). The stdlib service remains the zero-dependency
reference; this is the deployable variant.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import audit as audit_mod
from . import auth as auth_mod
from . import engine
from . import llm as llm_mod
from .capstone import TriageCapstone
from .exam import ExamSimulator
from .progress import BADGE_DEFS, ProgressStore
from .report import ReportReviewer
from .service import GraderState, _public_manifest
from .tutor import Tutor
from .validator import ChallengeValidator

_LABS_DIR = Path(__file__).resolve().parent.parent / "labs"
_STATIC_DIR = Path(__file__).resolve().parent / "static"


class Event(BaseModel):
    role: str
    source: str = "chat_ui"
    content: str = ""


class SubmitRequest(BaseModel):
    learner_id: str
    transcript: List[Event] = Field(default_factory=list)
    flag: str = ""
    attempt: int = 0


class AskRequest(BaseModel):
    query: str
    mode: str = "tutor"


class ReviewRequest(BaseModel):
    finding: dict
    transcript: List[Event] = Field(default_factory=list)


class ExamStartRequest(BaseModel):
    learner_id: str
    lab_ids: Optional[List[str]] = None
    duration_seconds: Optional[int] = None


class ExamSubmitRequest(BaseModel):
    lab_id: str
    transcript: List[Event] = Field(default_factory=list)
    flag: str = ""
    finding: dict = Field(default_factory=dict)


class ReviewCardRequest(BaseModel):
    card_id: int
    grade: int


class CapstoneSubmitRequest(BaseModel):
    findings: List[dict] = Field(default_factory=list)
    escalation_chain: bool = False


class AuthRequest(BaseModel):
    username: str
    password: str


def _dump(event: Event) -> dict:
    return event.model_dump() if hasattr(event, "model_dump") else event.dict()


def create_app(seed: str | None = None, labs_dir=None) -> FastAPI:
    auth_mod.enforce_deploy_policy()  # fail closed on an insecure public deployment
    state = GraderState(
        seed or os.environ.get("OSAI_SERVER_SEED", "dev-seed-change-me"),
        labs_dir or _LABS_DIR,
    )
    app = FastAPI(title="OSAI Prep Studio — Grader", version="0.1.0")
    provider = llm_mod.LLMProvider() if llm_mod.enabled() else None
    tutor = Tutor(registry=state.registry, llm=provider)
    progress = ProgressStore(os.environ.get("OSAI_DB", ":memory:"))
    reviewer = ReportReviewer(state.registry)
    exam = ExamSimulator(state, reviewer, progress)
    capstone = TriageCapstone()
    auth = auth_mod.AuthStore(
        os.environ.get("OSAI_AUTH_DB", ":memory:"),
        secret=os.environ.get("OSAI_AUTH_SECRET") or state.seed,
    )
    audit_log = audit_mod.AuditLog(os.environ.get("OSAI_AUDIT_DB", ":memory:"))

    def resolve_learner(body_learner: str, authorization):
        """When auth is enabled, the effective learner is the verified token subject —
        a user can only act as themselves. When disabled (default), the client-supplied
        id is used, so offline/demo/CI flows are unchanged."""
        if not auth_mod.auth_enabled():
            return body_learner
        token = ""
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        sub = auth.verify_token(token)
        if not sub:
            raise HTTPException(status_code=401, detail="authentication required")
        return sub

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (_STATIC_DIR / "index.html").read_text(encoding="utf-8")

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "engine": engine.ENGINE_PATH,
            "labs": sorted(state.labs),
            "tutor_corpus_chunks": len(tutor.library.chunks),
            "llm": llm_mod.status(),
            "auth_enabled": auth_mod.auth_enabled(),
        }

    @app.post("/auth/register")
    def auth_register(req: AuthRequest):
        try:
            user = auth.register(req.username, req.password)
        except auth_mod.AuthError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        audit_log.record(audit_mod.AUTH_REGISTER, user)
        return {"learner_id": user, "token": auth.issue_token(user)}

    @app.post("/auth/login")
    def auth_login(req: AuthRequest):
        try:
            ok = auth.authenticate(req.username, req.password)
        except auth_mod.LoginThrottled:
            audit_log.record(audit_mod.AUTH_LOGIN_THROTTLED, req.username)
            raise HTTPException(status_code=429, detail="too many attempts; try again later")
        if not ok:
            audit_log.record(audit_mod.AUTH_LOGIN_FAILURE, req.username)
            raise HTTPException(status_code=401, detail="invalid credentials")
        audit_log.record(audit_mod.AUTH_LOGIN, req.username)
        return {"learner_id": req.username, "token": auth.issue_token(req.username)}

    @app.post("/auth/logout")
    def auth_logout(authorization: str | None = Header(default=None)):
        learner = resolve_learner("", authorization) if auth_mod.auth_enabled() else ""
        if learner:
            auth.revoke_sessions(learner)  # invalidates every outstanding token
            audit_log.record(audit_mod.AUTH_LOGOUT, learner)
        return {"ok": True}

    @app.get("/auth/me")
    def auth_me(authorization: str | None = Header(default=None)):
        if not auth_mod.auth_enabled():
            return {"auth_enabled": False, "learner_id": None}
        return {"auth_enabled": True, "learner_id": resolve_learner("", authorization)}

    @app.get("/auth/events")
    def auth_events(authorization: str | None = Header(default=None)):
        # a learner's own recent audit trail (instructor-wide view is a future admin role)
        if not auth_mod.auth_enabled():
            return {"events": []}
        return {"events": audit_log.recent(50, actor=resolve_learner("", authorization))}

    @app.get("/catalog")
    def catalog():
        r = state.registry
        return {
            "detectors": r.detector_names(),
            "owasp_llm_2025": r.owasp,
            "owasp_agentic": r.agentic,
        }

    @app.get("/labs")
    def labs():
        return [
            {"id": m["id"], "title": m["title"], "difficulty": m.get("difficulty")}
            for m in state.labs.values()
        ]

    @app.get("/labs/{lab_id}")
    def lab(lab_id: str):
        manifest = state.labs.get(lab_id)
        if not manifest:
            raise HTTPException(status_code=404, detail="no such lab")
        return _public_manifest(manifest)

    @app.post("/labs/{lab_id}/submit")
    def submit(lab_id: str, req: SubmitRequest, authorization: str | None = Header(default=None)):
        manifest = state.labs.get(lab_id)
        if not manifest:
            raise HTTPException(status_code=404, detail="no such lab")
        learner = resolve_learner(req.learner_id, authorization)
        transcript = [_dump(e) for e in req.transcript]
        result = ChallengeValidator(manifest).grade(
            transcript, req.flag, state.seed, learner, req.attempt
        )
        feedback = result.public_feedback()
        feedback["progress"] = progress.record_attempt(learner, manifest, result)
        new_badges = progress.award_badges(learner, state.registry)
        if new_badges:
            feedback["new_badges"] = new_badges
        audit_log.record(audit_mod.LAB_SUBMIT, learner, {"lab": lab_id, "passed": result.passed})
        return feedback

    @app.get("/progress/{learner_id}")
    def get_progress(learner_id: str, authorization: str | None = Header(default=None)):
        return progress.summary(resolve_learner(learner_id, authorization), state.registry)

    @app.get("/readiness/{learner_id}")
    def get_readiness(learner_id: str, authorization: str | None = Header(default=None)):
        return progress.readiness(resolve_learner(learner_id, authorization), state.registry)

    @app.get("/badges/{learner_id}")
    def get_badges(learner_id: str, authorization: str | None = Header(default=None)):
        return {"earned": progress.badges(resolve_learner(learner_id, authorization)),
                "catalog": BADGE_DEFS}

    @app.get("/leaderboard")
    def leaderboard(limit: int = 10):
        return progress.leaderboard(state.registry, limit)

    @app.post("/flashcards/{learner_id}/seed")
    def seed_cards(learner_id: str, authorization: str | None = Header(default=None)):
        learner = resolve_learner(learner_id, authorization)
        return {"created": progress.seed_weakness_cards(learner, state.registry)}

    @app.get("/flashcards/{learner_id}/due")
    def due_cards(learner_id: str, authorization: str | None = Header(default=None)):
        return progress.due_cards(resolve_learner(learner_id, authorization))

    @app.post("/flashcards/review")
    def review_card(req: ReviewCardRequest):
        try:
            return progress.review_card(req.card_id, req.grade)
        except KeyError:
            raise HTTPException(status_code=404, detail="no such flashcard")

    @app.post("/tutor/ask")
    def tutor_ask(req: AskRequest):
        return tutor.ask(req.query, req.mode)

    @app.post("/reports/review")
    def review_report(req: ReviewRequest):
        transcript = [_dump(e) for e in req.transcript] or None
        return reviewer.review(req.finding, transcript).to_dict()

    @app.post("/exam/start")
    def exam_start(req: ExamStartRequest, authorization: str | None = Header(default=None)):
        learner = resolve_learner(req.learner_id, authorization)
        return exam.start_session(learner, req.lab_ids, req.duration_seconds)

    @app.post("/exam/{session_id}/submit")
    def exam_submit(session_id: str, req: ExamSubmitRequest):
        try:
            return exam.submit(session_id, req.lab_id, [_dump(e) for e in req.transcript],
                               req.flag, req.finding or None)
        except KeyError:
            raise HTTPException(status_code=404, detail="no such exam session")

    @app.get("/exam/{session_id}/score")
    def exam_score(session_id: str):
        try:
            return exam.score(session_id, state.registry)
        except KeyError:
            raise HTTPException(status_code=404, detail="no such exam session")

    @app.get("/capstone")
    def capstone_brief():
        return capstone.public_brief()

    @app.post("/capstone/score")
    def capstone_score(req: CapstoneSubmitRequest):
        return capstone.score({"findings": req.findings, "escalation_chain": req.escalation_chain})

    return app


# Module-level app for `uvicorn osai_spine.api:app`
app = create_app()
