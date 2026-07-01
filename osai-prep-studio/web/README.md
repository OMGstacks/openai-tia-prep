# OSAI Prep Studio — Web Front-End (Next.js)

A Next.js (App Router, TypeScript) front-end for the OSAI Prep Studio grader. It is a
**thin, typed client** over the FastAPI backend (`osai_spine.api`) — all the logic
(grading, tutor, progress, capstone) lives server-side; this renders it and drives the
learner loop. It supersedes the single-file `spine/osai_spine/static/index.html` demo
UI with a componentized, buildable app.

## Architecture

```
browser ──/api/*──▶ Next server (rewrite proxy) ──▶ FastAPI grader (osai_spine.api)
```

The browser only ever calls `/api/*` on the Next origin; `next.config.js` proxies that
to the grader (`OSAI_API_URL`, default `http://localhost:8077`). No CORS, and the
grader URL is configurable per environment.

## Run it

```bash
# 1) start the grader (from the repo root)
cd osai-prep-studio/spine
pip install -r requirements.txt
PYTHONPATH=. uvicorn osai_spine.api:app --port 8077

# 2) start the web app (separate shell)
cd osai-prep-studio/web
cp .env.example .env.local        # optional: point OSAI_API_URL elsewhere
npm install
npm run dev                       # http://localhost:3000
```

`npm run typecheck` runs `tsc --noEmit`; `npm run build` produces the production build.

## What's here

Multi-route App-Router app with a shared top nav and a shared learner (persisted to
localStorage). Routes: `/` (home), `/labs`, `/tutor`, `/progress`, `/exam`, `/capstone`,
`/login`.

**Auth (optional).** When the server has `OSAI_AUTH=1`, the header shows **Sign in**
(`/login` → register or log in); on success the session token is stored and attached as
`Authorization: Bearer` on every request, so the server derives your learner from the
token. When auth is off, the header keeps the free-text learner input. The token is
never sent to a third party — only to the grader.

| Path | Role |
|---|---|
| `app/layout.tsx` + `components/AppShell.tsx` | Shell: top nav (active-route aware), the learner input, health/AI-status banner, and the `<main>` grid |
| `lib/learner.tsx` | `LearnerProvider` + `useLearner()` — shared learner id across routes |
| `app/page.tsx` | Home — section cards linking to each route |
| `app/labs/page.tsx` → `LabsPanel` | Attack a lab → two-signal grade → new-badge surfacing |
| `app/tutor/page.tsx` → `TutorPanel` | Ask the tutor; renders grounded / abstained / refused + citations |
| `app/progress/page.tsx` → `ProgressPanel` + `FlashcardsPanel` + `LeaderboardPanel` | Mastery/readiness/heatmap/badges, SRS drill, and the leaderboard |
| `app/exam/page.tsx` → `ExamRoom` | **Exam mode** — timed multi-target engagement, per-target attack + finding, live countdown, scored report + retake plan |
| `app/capstone/page.tsx` → `CapstonePanel` | L20 triage: read the incident log, submit findings, see the score |
| `lib/api.ts`, `lib/types.ts` | Typed client + response shapes (mirrors the server's redacted contract) |

## Notes

- **Answer-key safety is server-side.** The client only receives the grader's public
  (redacted) responses — no expected detector, OWASP id, or capstone answer key is ever
  sent to the browser.
- **Resilient UX.** If the grader is unreachable a connection banner appears with the fix
  (`uvicorn osai_spine.api:app --port 8077`) and a retry; read panels (`useApi` hook) show
  loading / error / empty states; action panels surface submit/ask errors inline; the
  layout is responsive (`viewport` meta + an auto-fit grid).
- The **generative tutor** lights up automatically when the backend has the LLM layer
  enabled (the header shows `AI tutor ✓`); otherwise the offline extractive tutor is
  used — the UI is identical either way.
- Dependencies are installed at `npm install` time and are **not** committed
  (`node_modules/`, `.next/` are git-ignored). This is a scaffold: run it locally or in
  a Node environment; it is intentionally not wired into the stdlib Python CI.
