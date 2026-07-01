// Typed client for the FastAPI grader. All calls go through /api/* which Next
// proxies to the grader (see next.config.js) — no CORS, URL configurable.
import type {
  AuthResponse,
  CapstoneBrief,
  CapstoneScore,
  ExamScore,
  ExamSession,
  ExamSubmitResult,
  Flashcard,
  Health,
  LabSummary,
  LeaderboardRow,
  Progress,
  ReviewResult,
  SubmitResult,
  TutorAnswer,
} from "./types";

// Attach the session token (when auth is enabled and the learner has logged in) so
// the server derives the learner from the token, not the request body.
function authHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const t = window.localStorage.getItem("osai_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function j<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...opts,
    headers: { ...(opts.headers || {}), ...authHeader() },
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return (await res.json()) as T;
}

function post<T>(path: string, body: unknown): Promise<T> {
  return j<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export interface Transcript {
  role: string;
  source: string;
  content: string;
}

export const api = {
  health: () => j<Health>("/health"),
  register: (username: string, password: string) =>
    post<AuthResponse>("/auth/register", { username, password }),
  login: (username: string, password: string) =>
    post<AuthResponse>("/auth/login", { username, password }),
  logout: () => post<{ ok: boolean }>("/auth/logout", {}),
  labs: () => j<LabSummary[]>("/labs"),
  submit: (lab: string, learner_id: string, transcript: Transcript[], flag: string) =>
    post<SubmitResult>(`/labs/${lab}/submit`, { learner_id, transcript, flag }),
  tutorAsk: (query: string) => post<TutorAnswer>("/tutor/ask", { query }),
  progress: (learner: string) => j<Progress>(`/progress/${learner}`),
  seedCards: (learner: string) => post<{ created: number[] }>(`/flashcards/${learner}/seed`, {}),
  dueCards: (learner: string) => j<Flashcard[]>(`/flashcards/${learner}/due`),
  reviewCard: (card_id: number, grade: number) =>
    post<ReviewResult>("/flashcards/review", { card_id, grade }),
  leaderboard: () => j<LeaderboardRow[]>("/leaderboard"),
  examStart: (learner_id: string, lab_ids?: string[]) =>
    post<ExamSession>("/exam/start", { learner_id, lab_ids }),
  examSubmit: (
    sid: string,
    lab_id: string,
    transcript: Transcript[],
    flag: string,
    finding: Record<string, unknown>,
  ) => post<ExamSubmitResult>(`/exam/${sid}/submit`, { lab_id, transcript, flag, finding }),
  examScore: (sid: string) => j<ExamScore>(`/exam/${sid}/score`),
  capstone: () => j<CapstoneBrief>("/capstone"),
  capstoneScore: (findings: { owasp_id: string }[], escalation_chain: boolean) =>
    post<CapstoneScore>("/capstone/score", { findings, escalation_chain }),
};
