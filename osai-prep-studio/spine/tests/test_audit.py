"""Append-only audit log: records events, filters by actor, never stores secrets."""

from osai_spine import audit


def test_record_and_recent_filtered_by_actor():
    log = audit.AuditLog()
    log.record(audit.AUTH_REGISTER, "alice", now=1.0)
    log.record(audit.AUTH_LOGIN, "alice", now=2.0)
    log.record(audit.LAB_SUBMIT, "bob", {"lab": "L01", "passed": True}, now=3.0)

    alice = log.recent(actor="alice")
    assert {e["event"] for e in alice} == {"auth.register", "auth.login"}
    assert alice[0]["event"] == "auth.login"  # most recent first

    everyone = log.recent()
    assert len(everyone) == 3
    bob = [e for e in everyone if e["actor"] == "bob"][0]
    assert bob["detail"] == {"lab": "L01", "passed": True}
