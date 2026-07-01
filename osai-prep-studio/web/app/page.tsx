import Link from "next/link";

const CARDS = [
  { href: "/labs", title: "Labs", body: "Attack the range and get two-signal graded — the detector must fire and you must produce the evidence flag." },
  { href: "/tutor", title: "Tutor", body: "Ask grounded, cited questions. Abstains with no source; refuses real-world targets. Goes generative when the LLM key is live." },
  { href: "/progress", title: "Progress", body: "Mastery, readiness, weakness heatmap, achievement badges, the leaderboard, and spaced-repetition flashcards." },
  { href: "/exam", title: "Exam", body: "A timed multi-target engagement: attack each target, submit a graded finding, and get the weighted score + retake plan." },
  { href: "/capstone", title: "Capstone", body: "Flip to the defender — triage a mixed incident log; scored on OWASP precision/recall and the escalation chain." },
];

export default function Home() {
  return (
    <>
      <section className="panel" style={{ gridColumn: "1 / -1" }}>
        <h2>OSAI Prep Studio — AI-300 / OSAI training range</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          A reuse-first, authorized-lab-only range for AI red teaming. Pick a section to
          begin; set your learner name in the header (it persists locally).
        </p>
      </section>
      {CARDS.map((c) => (
        <Link key={c.href} href={c.href} className="panel" style={{ textDecoration: "none", color: "inherit" }}>
          <h2>{c.title}</h2>
          <div>{c.body}</div>
        </Link>
      ))}
    </>
  );
}
