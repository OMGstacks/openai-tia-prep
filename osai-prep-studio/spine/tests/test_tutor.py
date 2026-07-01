"""Retrieval-grounded tutor: retrieval, abstention, citations, anti-hallucination."""

from osai_spine.taxonomy import TaxonomyRegistry
from osai_spine.tutor import SourceLibrary, Tutor, validate_taxonomy_ids


def _tutor():
    return Tutor(library=SourceLibrary(), registry=TaxonomyRegistry())


def test_corpus_loads():
    lib = SourceLibrary()
    assert len(lib.chunks) > 10  # the reference docs chunk into many sections


def test_in_corpus_query_is_grounded_and_cited():
    res = _tutor().ask("What is prompt injection and how does indirect injection work?")
    assert res["abstained"] is False
    assert res["answer"]
    assert res["citations"], "a grounded answer must carry citations"
    assert all(c["source"].startswith("reference/") for c in res["citations"])
    assert res.get("taxonomy_ids_valid", True) is True


def test_out_of_corpus_query_abstains():
    res = _tutor().ask("What is the best recipe for sourdough bread at high altitude?")
    assert res["abstained"] is True
    assert res["citations"] == []


def test_taxonomy_id_validation():
    reg = TaxonomyRegistry()
    text = "Real ids LLM01:2025 and AML.T0051.000; fake id LLM99:2025."
    assert validate_taxonomy_ids(text, reg) == ["LLM99:2025"]
    assert validate_taxonomy_ids("LLM05:2025 AML.T0024", reg) == []


def test_long_section_mitigation_is_indexed_not_truncated():
    # regression: the LLM01 mitigation paragraph sits past the old 1600-char cap;
    # section-splitting must keep it as its own retrievable chunk.
    lib = SourceLibrary()
    assert any("Programmatic mitigation" in c.text and c.section == "LLM01:2025" for c in lib.chunks)


def test_defense_intent_query_retrieves_mitigation():
    # regression: "how do I defend" must reach the corpus's "mitigation" content
    # (query-expansion + weighting bridge the vocabulary gap).
    lib = SourceLibrary()
    hits = lib.retrieve("how do I defend against indirect prompt injection", 5)
    assert any(
        "mitigation" in c.text.lower() or "trust boundary" in c.text.lower() for _s, c in hits
    )


def test_citations_carry_authority_tier():
    res = _tutor().ask("excessive agency and tool invocation")
    if not res["abstained"]:
        assert all("tier" in c for c in res["citations"])
