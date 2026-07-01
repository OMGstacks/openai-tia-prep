from osai_spine.taxonomy import TaxonomyRegistry


def test_registry_loads_nine_detectors():
    reg = TaxonomyRegistry()
    names = reg.detector_names()
    assert len(names) == 9
    for expected in [
        "direct_prompt_injection",
        "indirect_prompt_injection",
        "system_prompt_extraction",
        "sensitive_information_disclosure",
        "improper_output_handling",
    ]:
        assert expected in names


def test_owasp_canonical_complete():
    reg = TaxonomyRegistry()
    assert len(reg.owasp) == 10
    assert reg.is_owasp("LLM01:2025")
    assert reg.is_owasp("LLM10:2025")
    assert not reg.is_owasp("LLM99:2025")


def test_agentic_threats_t1_t15():
    reg = TaxonomyRegistry()
    assert len(reg.agentic) == 15
    assert reg.is_agentic("T1")
    assert reg.is_agentic("T15")
    assert not reg.is_agentic("T16")


def test_atlas_form_validation():
    reg = TaxonomyRegistry()
    assert reg.is_atlas("AML.T0051.000")
    assert reg.is_atlas("AML.T0056")
    assert reg.is_atlas("AML.TA0002")
    assert not reg.is_atlas("T0051")
    assert not reg.is_atlas("nonsense")


def test_valid_and_invalid_tags():
    reg = TaxonomyRegistry()
    assert reg.is_valid_tag("direct_prompt_injection")
    assert reg.is_valid_tag("LLM05:2025")
    assert reg.is_valid_tag("AML.T0024")
    assert reg.is_valid_tag("T2")
    assert reg.invalid_tags(["LLM01:2025", "bogus", "T99"]) == ["bogus", "T99"]


def test_detector_owasp_crosswalk():
    reg = TaxonomyRegistry()
    assert reg.owasp_for_detector("direct_prompt_injection") == "LLM01:2025"
    assert reg.owasp_for_detector("system_prompt_extraction") == "LLM07:2025"
