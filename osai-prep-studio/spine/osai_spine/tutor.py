"""Retrieval-grounded tutor core (pillar 6) — the offline-verifiable foundation of
03-tutor-examiner-bot.md.

Realizes the load-bearing properties without an LLM call, so it runs and is tested
in CI:
  * retrieval-first over a curated Source Library (09a-source-library.md),
  * "no source, no confident answer" abstention,
  * citation enforcement (every grounded answer carries its sources + tiers),
  * taxonomy anti-hallucination (any LLMxx/AML.Txxxx the answer mentions must be real).

The answer is **extractive** here (grounded passage + citations); a generative LLM
can be slotted in behind the same ``Tutor.ask`` seam later (the retrieval, grounding
gate, citation, and validation stay identical). Stdlib-only TF-IDF retrieval.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

# (path relative to repo root, authority tier) — see 09a-source-library.md
DEFAULT_SOURCES = [
    ("reference/owasp-llm-top-10.md", "A1"),
    ("reference/mitre-atlas.md", "A1"),
    ("reference/owasp-agentic-threats.md", "A1"),
    ("reference/nist-ai-rmf.md", "A1"),
    ("reference/ai-redteam-tooling.md", "A2"),
    ("reference/osai-studio-architecture.md", "A3"),
    ("reference/agentic-tool-use-decisions.md", "A3"),
    ("reference/glossary.md", "A3"),
]

ABSTAIN_THRESHOLD = 0.07  # min cosine similarity to answer rather than abstain
# Ignore very-common terms (idf below this) so generic words like "what/the/high"
# don't create spurious similarity — only distinctive content terms drive retrieval.
IDF_FLOOR = 1.8
# Long reference sections are split into paragraph-level sub-chunks at ~this size, so
# no content (e.g. a section's mitigation paragraph) is dropped by truncation and each
# aspect (what / attack / detection / mitigation) is independently retrievable.
CHUNK_MAX_CHARS = 1100

_WORD = re.compile(r"[a-z0-9]+")
_TAXONOMY_ID = re.compile(r"\bLLM\d{2}:2025\b|\bAML\.T(?:A)?\d{4}(?:\.\d{3})?\b")

# Bridge a common vocabulary gap: learners ask how to "defend", the reference corpus
# labels the answer "mitigation" / "prevention". Expanding the query with the corpus's
# own terms (weighted, so the mitigation chunk actually outranks the definition chunks)
# lets TF-IDF retrieval reach the mitigation content (a stopgap for the stdlib
# retriever; semantic embeddings are the product-grade fix, 07-arch §RAG).
_EXPANSION_BOOST = 3
_QUERY_EXPANSIONS = {
    "defend": ["mitigation", "prevention"],
    "defense": ["mitigation", "prevention"],
    "defence": ["mitigation", "prevention"],
    "defending": ["mitigation", "prevention"],
    "protect": ["mitigation", "prevention"],
    "prevent": ["mitigation", "prevention"],
    "prevention": ["mitigation"],
    "mitigate": ["mitigation"],
    "remediate": ["mitigation", "remediation"],
    "harden": ["mitigation", "hardening"],
    "stop": ["mitigation", "prevention"],
    "guard": ["mitigation", "prevention"],
    "countermeasure": ["mitigation"],
}

# Generic English filler — dropped so it can't ground a security answer. (Domain
# terms like "high"/"injection" are deliberately NOT here; the IDF floor + the
# >=2-distinctive-overlap rule handle those.)
_STOPWORDS = frozenset("""
a an the is are was were be been being am do does did doing have has had having
what which who whom whose how why when where this that these those it its
to of in on for with and or but if then else at by from as about into over under
again i you your yours we our ours they them their he she his her my me mine us
can could should would will shall may might must not no nor yes so than too very
just only also more most less least some any all each both few many much such own
same other another please tell show explain describe give get make use using best
good better worst great recipe bread how's let lets want need know
""".split())


def _tokenize(text: str):
    return [w for w in _WORD.findall(text.lower()) if w not in _STOPWORDS]


def validate_taxonomy_ids(text: str, registry) -> list:
    """Return any framework ids in ``text`` that are NOT real (anti-hallucination)."""
    bad = []
    for tid in _TAXONOMY_ID.findall(text):
        if tid.startswith("LLM"):
            if not registry.is_owasp(tid):
                bad.append(tid)
        elif not registry.is_atlas(tid):
            bad.append(tid)
    return bad


class _Chunk:
    __slots__ = ("source", "title", "text", "tier", "section", "tf")

    def __init__(self, source, title, text, tier, section=None):
        self.source = source
        self.title = title
        self.text = text
        self.tier = tier
        self.section = section  # nearest enclosing framework id (e.g. LLM01:2025), if any
        self.tf = Counter(_tokenize(title + " " + text))


def _split_markdown(md_text: str):
    """Split a markdown doc into (heading, body, section_id) sections. ``section_id``
    is the nearest enclosing heading that names a framework id (LLMxx:2025 / AML.T...),
    so a chunk retrieved from a sub-section still reports which category it belongs to."""
    sections, title, buf, section = [], "(intro)", [], None
    for line in md_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            if buf:
                sections.append((title, "\n".join(buf), section))
                buf = []
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped.lstrip("#").strip() or title
            found = _TAXONOMY_ID.findall(line)
            if found:
                section = found[0]   # entering a framework-tagged section
            elif level <= 2:
                section = None       # a new top-level, non-framework section -> reset
            # deeper (###+) non-id headings inherit the enclosing section
        else:
            buf.append(line)
    if buf:
        sections.append((title, "\n".join(buf), section))
    return sections


def _split_body(body: str, max_chars: int = CHUNK_MAX_CHARS):
    """Greedily pack a section's paragraphs into sub-chunks of at most ``max_chars``,
    so a long section becomes several retrievable chunks instead of one truncated one.
    A single oversized paragraph becomes its own chunk (never dropped)."""
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    chunks, cur = [], ""
    for para in paras:
        if cur and len(cur) + len(para) + 2 > max_chars:
            chunks.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        chunks.append(cur)
    return chunks or [body]


class SourceLibrary:
    """A small TF-IDF index over curated markdown sources."""

    def __init__(self, sources=None, root=None):
        # OSAI_CORPUS_ROOT lets a container relocate the source corpus.
        self.root = Path(root or os.environ.get("OSAI_CORPUS_ROOT") or _REPO_ROOT)
        self.chunks: list[_Chunk] = []
        for rel, tier in (sources or DEFAULT_SOURCES):
            path = self.root / rel
            if not path.is_file():
                continue
            for title, body, section in _split_markdown(path.read_text(encoding="utf-8")):
                body = body.strip()
                if len(body) < 40:
                    continue
                for sub in _split_body(body):
                    if len(sub) >= 40:
                        self.chunks.append(_Chunk(rel, title, sub, tier, section))
        self._build_idf()

    def _build_idf(self):
        n = len(self.chunks) or 1
        df = Counter()
        for chunk in self.chunks:
            for term in set(chunk.tf):
                df[term] += 1
        self.idf = {t: math.log((n + 1) / (d + 1)) + 1 for t, d in df.items()}

    def _vector(self, tf):
        return {
            t: f * self.idf[t]
            for t, f in tf.items()
            if self.idf.get(t, 0.0) >= IDF_FLOOR
        }

    def distinctive_terms(self, text: str) -> set:
        return {t for t in _tokenize(text) if self.idf.get(t, 0.0) >= IDF_FLOOR}

    def distinctive_overlap(self, query: str, chunk) -> int:
        chunk_terms = {t for t in chunk.tf if self.idf.get(t, 0.0) >= IDF_FLOOR}
        return len(self.distinctive_terms(query) & chunk_terms)

    def retrieve(self, query: str, k: int = 3):
        tokens = _tokenize(query)
        for term in list(tokens):  # bridge defense-intent asks to the corpus's "mitigation" vocab
            for exp in _QUERY_EXPANSIONS.get(term, []):
                tokens.extend([exp] * _EXPANSION_BOOST)
        q = self._vector(Counter(tokens))
        qn = math.sqrt(sum(v * v for v in q.values())) or 1.0
        scored = []
        for chunk in self.chunks:
            cv = self._vector(chunk.tf)
            cn = math.sqrt(sum(v * v for v in cv.values())) or 1.0
            dot = sum(q.get(t, 0.0) * v for t, v in cv.items())
            scored.append((dot / (qn * cn), chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]


def _lead(text: str, limit: int = 600) -> str:
    text = " ".join(text.split())
    return text[:limit] + ("…" if len(text) > limit else "")


# Authorized-lab-only scope guard (11-safety-legal-ethics.md, 04-evaluation-harness.md
# §6). The tutor coaches technique against the training range and authorized labs only:
# it refuses to help attack real/external/production systems and refuses to surface a
# lab's flags, answer keys, or solutions. These are deterministic, offline checks so
# the refusal gate holds with or without an LLM.
_ATTACK_VERB = re.compile(
    r"\b(attack|exploit|hack|jailbreak|phish|exfiltrat|bypass|compromise|pwn|ddos|"
    r"breach|backdoor|takeover|take[\s-]?over|deface|infiltrat|weaponiz|steal|poison|"
    r"brute[\s-]?forc|credentials?[\s-]?stuff|ransomware|botnet|scrape|crack|"
    r"break[\s-]?in|leak)\w*", re.I)
_REAL_TARGET = re.compile(
    r"\b(openai|chatgpt|gpt-?[45]|gemini|bard|copilot|anthropic|claude\.ai|google|"
    r"gmail|microsoft|azure|aws|amazon|facebook|meta|salesforce|okta|github|"
    r"production|prod|"
    r"real (?:company|companies|customer|client|user|system|world|bank|hospital|"
    r"business|org|organization|website|site|app|service|model|endpoint|target|"
    r"person|people|employee|employees|employer|login|api|infrastructure)|"
    r"live (?:system|site|target|api|model|chatbot|endpoint|service|app|server|"
    r"account|backend|infrastructure)|in the wild|"
    r"(?:ex[\s-]?)?employer|competitor|"
    r"another (?:user|customer|person|company|organization|org)|someone else|"
    r"other (?:users|people|customers)|"
    r"my (?:employer|company|bank|org|organization))\b", re.I)
_LAB_SCOPE = re.compile(
    r"\b(lab|labs|megacorp|mock|sandbox|authoriz|range|exercise|L0\d|L1\d)\w*", re.I)
_ANSWER_KEY = re.compile(r"\b(flag|flags|answer[ -]?key|solution|cheat)\w*", re.I)


def scope_refusal(query: str):
    """Return a refusal message if the query is out of the authorized-lab scope,
    else ``None``. Two cases: answer-key/flag elicitation tied to a lab, and helping
    to attack a real/external/production target."""
    q = query or ""
    if _ANSWER_KEY.search(q) and (_LAB_SCOPE.search(q) or "OSAI{" in q):
        return ("I won't reveal lab flags, answer keys, or solutions — that defeats the "
                "exercise. Ask me to explain the underlying technique instead.")
    if _ATTACK_VERB.search(q) and _REAL_TARGET.search(q) and not _LAB_SCOPE.search(q):
        return ("Authorized-lab scope only: I can't help attack real, external, or "
                "production systems. I coach these techniques against the training "
                "range and authorized labs.")
    return None


_GROUNDED_SYSTEM = (
    "You are the OSAI Prep Studio tutor for authorized AI red-team exam prep. "
    "Answer ONLY from the numbered SOURCES; if they don't support an answer, say so "
    "plainly. Never invent OWASP LLMxx:2025 or MITRE ATLAS (AML.T...) ids — use only "
    "ids that appear in the sources. Be concise and cite sources by their [n] tag. "
    "Authorized-lab scope only: refuse to help attack any real or non-lab system."
)


class Tutor:
    """Retrieval-first, citation-enforced, abstaining tutor.

    The answer is **extractive** by default (grounded passage + citations), which is
    what runs in CI. When an optional ``llm`` provider is supplied and usable, the
    same grounded hits are handed to Claude to compose a fluent answer *strictly from
    those sources* — the retrieval gate, abstention, citations, and taxonomy
    validation are unchanged, and any failure falls back to the extractive answer.
    """

    def __init__(self, library=None, registry=None, llm=None):
        self.library = library or SourceLibrary()
        self.registry = registry
        self.llm = llm  # optional LLMProvider; None -> extractive (default)

    def ask(self, query: str, mode: str = "tutor", k: int = 5) -> dict:
        # Stale-claim check (Bank Expansion Epic Phase 3): flag version-sensitive/outdated
        # claims against current ground truth and name the fresher fact, so the tutor
        # caveats rather than repeats a stale claim. Deterministic, no retrieval.
        if mode == "stale":
            from .staleness import check_claim
            v = check_claim(query)
            return {
                "refused": False, "abstained": False, "mode": mode,
                "stale": v["stale"], "fresher": v["fresher"], "guidance": v["guidance"],
                "answer": v["fresher"] or "No stale claim detected; the statement reflects current framework/studio state.",
                "citations": [],
            }
        # Safety scope guard runs before retrieval — refusals never touch the corpus.
        refusal = scope_refusal(query)
        if refusal:
            return {
                "refused": True,
                "abstained": False,
                "mode": mode,
                "answer": refusal,
                "citations": [],
            }
        hits = self.library.retrieve(query, k)
        top = hits[0][0] if hits else 0.0
        # A lone common-ish term must not ground a security answer: require >=2
        # distinctive shared terms, unless the single-term match is strong.
        overlap = self.library.distinctive_overlap(query, hits[0][1]) if hits else 0
        grounded = bool(hits) and top >= ABSTAIN_THRESHOLD and (overlap >= 2 or top >= 0.35)

        # Grounding gate — "no source, no confident answer".
        if not grounded:
            return {
                "abstained": True,
                "refused": False,
                "mode": mode,
                "answer": (
                    "No source in the library supports a confident answer. Rephrase, "
                    "or add a source to the corpus — I will not guess on security facts."
                ),
                "citations": [],
                "top_score": round(top, 4),
            }

        best = hits[0][1]
        citations = [
            {"source": c.source, "title": c.title, "tier": c.tier,
             "section": c.section, "score": round(s, 4)}
            for s, c in hits
            if s >= ABSTAIN_THRESHOLD
        ]
        # Generative-but-grounded answer when an LLM is wired; else extractive.
        generated = self._compose(query, hits)
        answer = generated if generated is not None else _lead(best.text)
        result = {
            "abstained": False,
            "refused": False,
            "mode": mode,
            "answer": answer,
            "generative": generated is not None,
            "citations": citations,
            "top_score": round(top, 4),
        }
        # Anti-hallucination: any framework id in the answer must be real.
        if self.registry is not None:
            bad = validate_taxonomy_ids(answer, self.registry)
            result["taxonomy_ids_valid"] = not bad
            if bad:
                result["invalid_ids"] = bad
        return result

    def _compose(self, query, hits):
        """Compose a grounded answer from the retrieved ``hits`` via the LLM seam.
        Returns ``None`` to signal "use the extractive fallback" — when no provider
        is wired, the call errors, the output is empty, or the answer fails the
        taxonomy guard (a hallucinated framework id)."""
        if self.llm is None:
            return None
        corpus = "\n\n".join(
            f"[{i + 1}] ({c.source} — {c.title}, tier {c.tier})\n{c.text}"
            for i, (_s, c) in enumerate(hits)
        )
        try:
            text = self.llm.complete(
                _GROUNDED_SYSTEM,
                f"QUESTION: {query}\n\nAnswer only from the SOURCES and cite them by [n].",
                cached_prefix="SOURCES:\n" + corpus,
                max_tokens=700,
            )
        except Exception:
            return None
        if not text:
            return None
        if self.registry is not None and validate_taxonomy_ids(text, self.registry):
            return None  # rejected a hallucinated id -> fall back to extractive
        return text
