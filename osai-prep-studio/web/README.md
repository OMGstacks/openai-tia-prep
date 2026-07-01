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

| Path | Role |
|---|---|
| `app/layout.tsx`, `app/page.tsx`, `app/globals.css` | App-Router shell + dark theme |
| `app/exam/page.tsx` + `components/ExamRoom.tsx` | **Exam mode** (`/exam`) — start a timed multi-target engagement, attack each target + submit a finding, live countdown, then the scored report (findings + report weight) and retake plan |
| `components/Dashboard.tsx` | Learner state (localStorage), health banner, panel layout, link to Exam mode |
| `components/LabsPanel.tsx` | Attack a lab → two-signal grade → new-badge surfacing |
| `components/TutorPanel.tsx` | Ask the tutor; renders grounded / abstained / refused + citations |
| `components/ProgressPanel.tsx` | XP, readiness, weakness heatmap, badges |
| `components/LeaderboardPanel.tsx` | Cross-learner ranking |
| `components/FlashcardsPanel.tsx` | Spaced-repetition drill — seed from weakness, review (easy/hard/again) |
| `components/CapstonePanel.tsx` | L20 triage: read the incident log, submit findings, see the score |
| `lib/api.ts`, `lib/types.ts` | Typed client + response shapes (mirrors the server's redacted contract) |

## Notes

- **Answer-key safety is server-side.** The client only receives the grader's public
  (redacted) responses — no expected detector, OWASP id, or capstone answer key is ever
  sent to the browser.
- The **generative tutor** lights up automatically when the backend has the LLM layer
  enabled (the header shows `AI tutor ✓`); otherwise the offline extractive tutor is
  used — the UI is identical either way.
- Dependencies are installed at `npm install` time and are **not** committed
  (`node_modules/`, `.next/` are git-ignored). This is a scaffold: run it locally or in
  a Node environment; it is intentionally not wired into the stdlib Python CI.
