PY ?= python3

# Run the spine test suite (stdlib + pytest only).
test:
	$(PY) -m pytest -q

# Print the canonical taxonomy registry (detectors + OWASP + agentic).
catalog:
	$(PY) -m osai_spine.cli catalog

# Validate every lab manifest against the taxonomy registry (the binding rule).
validate:
	$(PY) -m osai_spine.cli validate-manifests

# Run the tutor gold-set ship gate (04-evaluation-harness.md). Exits non-zero on fail.
goldset:
	$(PY) -m osai_spine.cli goldset

# Run the HTTP grader service (Ctrl-C to stop).
serve:
	$(PY) -m osai_spine.cli serve

# Prove the full loop: attack -> vulnerable mock target -> two-signal grade.
loop:
	$(PY) -m pytest -q tests/test_end_to_end_loop.py

.PHONY: test catalog validate goldset serve loop
