// Response shapes from the FastAPI grader (osai_spine.api). Kept in sync with the
// server's public (answer-redacted) contract.

export interface AuthResponse {
  learner_id: string;
  token: string;
}

export interface Health {
  status: string;
  labs: string[];
  tutor_corpus_chunks: number;
  auth_enabled?: boolean;
  llm: {
    enabled: boolean;
    transcripts_enabled: boolean;
    sdk_installed: boolean;
    key_present: boolean;
    model_quality: string;
    model_bulk: string;
  };
}

export interface LabSummary {
  id: string;
  title: string;
  difficulty: string | null;
}

export interface Badge {
  code: string;
  title: string;
  desc: string;
}

export interface SubmitResult {
  lab_id: string;
  passed: boolean;
  signal_a: boolean;
  signal_b: boolean;
  feedback: string[];
  progress?: { xp: number; attempts: { total: number; passed: number } };
  new_badges?: Badge[];
}

export interface Citation {
  source: string;
  title: string;
  tier: string;
  section: string | null;
  score: number;
}

export interface TutorAnswer {
  abstained: boolean;
  refused: boolean;
  generative?: boolean;
  answer: string;
  citations: Citation[];
  top_score?: number;
}

export interface Readiness {
  score: number;
  of: number;
  avg_owasp_mastery: number;
  owasp_coverage: number;
}

export interface HeatmapEntry {
  name: string;
  mastery: number;
}

export interface Progress {
  learner_id: string;
  xp: number;
  attempts: { total: number; passed: number };
  mastery: Record<string, { mastery: number; reps: number }>;
  badges: Badge[];
  readiness?: Readiness;
  weakness_heatmap?: Record<string, HeatmapEntry>;
}

export interface LeaderboardRow {
  rank: number;
  learner_id: string;
  xp: number;
  passed: number;
  attempts: number;
  badges: number;
  readiness: number;
}

export interface CapstoneBrief {
  events: { role: string; source: string; content: string }[];
  task: string;
}

export interface ExamSession {
  session_id: string;
  learner_id: string;
  targets: string[];
  started_at: number;
  duration_seconds: number;
  deadline: number;
  submitted: string[];
}

export interface ExamSubmitResult {
  lab_id?: string;
  lab_passed?: boolean;
  report_total?: number;
  remaining?: number;
  rejected?: string;
}

export interface RetakeItem {
  lab: string;
  skill: string;
  reason: string;
  recommend: string;
}

export interface ExamScore {
  session_id: string;
  score: number;
  of: number;
  passed: boolean;
  findings: { passed: number; of: number; weight: number };
  report: { avg_pct: number; weight: number };
  missed_paths: string[];
  retake_plan?: RetakeItem[];
}

export interface Flashcard {
  id: number;
  skill_tag: string;
  prompt: string;
  answer: string;
  interval_days: number;
  reps: number;
  due_ts: number;
}

export interface ReviewResult {
  card_id: number;
  interval_days: number;
  reps: number;
  ef: number;
}

export interface CapstoneScore {
  score: number;
  of: number;
  passed: boolean;
  precision: number;
  recall: number;
  f1: number;
  escalation_correct: boolean;
  counts: { submitted: number; correct: number; missed: number; false_positive: number };
}
