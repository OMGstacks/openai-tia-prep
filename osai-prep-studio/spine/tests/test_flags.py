from osai_spine import flags

SEED = "test-seed-not-a-real-secret"


def test_flag_format_and_determinism():
    f1 = flags.derive_flag(SEED, "alice", "L01")
    f2 = flags.derive_flag(SEED, "alice", "L01")
    assert f1 == f2
    assert f1.startswith("OSAI{") and f1.endswith("}")


def test_per_learner_and_per_lab_uniqueness():
    assert flags.derive_flag(SEED, "alice", "L01") != flags.derive_flag(SEED, "bob", "L01")
    assert flags.derive_flag(SEED, "alice", "L01") != flags.derive_flag(SEED, "alice", "L02")
    assert flags.derive_flag(SEED, "alice", "L01", 0) != flags.derive_flag(SEED, "alice", "L01", 1)


def test_verify():
    good = flags.derive_flag(SEED, "alice", "L01")
    assert flags.verify_flag(SEED, "alice", "L01", good)
    assert flags.verify_flag(SEED, "alice", "L01", "  " + good + "  ")  # trims whitespace
    assert not flags.verify_flag(SEED, "alice", "L01", "OSAI{deadbeefdeadbeefdeadbeef}")
    assert not flags.verify_flag(SEED, "bob", "L01", good)  # another learner's flag
