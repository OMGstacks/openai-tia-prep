"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useLearner } from "@/lib/learner";
import type { Flashcard } from "@/lib/types";

export default function FlashcardsPanel() {
  const { learner } = useLearner();
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [note, setNote] = useState("");

  const loadDue = useCallback(() => {
    api
      .dueCards(learner || "demo")
      .then(setCards)
      .catch(() => setCards([]));
  }, [learner]);

  useEffect(() => {
    loadDue();
  }, [loadDue]);

  const seed = async () => {
    try {
      const r = await api.seedCards(learner || "demo");
      setNote(`seeded ${r.created.length} cards from your weak areas`);
      loadDue();
    } catch {
      setNote("could not seed cards");
    }
  };

  const grade = async (id: number, g: number) => {
    try {
      const r = await api.reviewCard(id, g);
      setNote(`card ${id}: next in ${r.interval_days}d (reps ${r.reps})`);
      loadDue();
    } catch {
      setNote("review failed");
    }
  };

  return (
    <section className="panel">
      <h2>Flashcards (spaced repetition)</h2>
      <div className="row">
        <button onClick={seed}>Seed from weakness</button>
        <button className="ghost" onClick={loadDue}>
          Show due
        </button>
        <span className="muted">{note}</span>
      </div>
      <div>
        {cards.length ? (
          cards.map((c) => (
            <div className="lab" key={c.id}>
              <div>{c.prompt}</div>
              <div className="row">
                <span className="muted">{c.skill_tag}</span>
                <button className="ghost" onClick={() => grade(c.id, 5)}>
                  easy
                </button>
                <button className="ghost" onClick={() => grade(c.id, 3)}>
                  hard
                </button>
                <button className="ghost" onClick={() => grade(c.id, 1)}>
                  again
                </button>
              </div>
            </div>
          ))
        ) : (
          <span className="muted">no cards due — seed from your weak areas</span>
        )}
      </div>
    </section>
  );
}
