"""
test_events.py — Automated tests for the Event State Machine.

Tests cover:
  A — Valid transitions
  B — Duplicate / Idempotency
  C — Delayed events
  D — Out-of-order events
  E — Property-style state safety (deterministic permutations)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from routers.events import AssessmentStateMachine

VALID_STATES = {"IDLE", "STARTED", "ANSWERING", "DISCONNECTED", "SUBMITTED"}

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def new_machine():
    return AssessmentStateMachine()


# ---------------------------------------------------------------------------
# CATEGORY A — Valid State Transitions
# ---------------------------------------------------------------------------

class TestValidTransitions:
    def test_idle_to_started(self):
        m = new_machine()
        r = m.process_event("START_EXAM", "E001")
        assert r["status"] == "PROCESSED"
        assert m.state == "STARTED"

    def test_started_to_answering(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        r = m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        assert r["status"] == "PROCESSED"
        assert m.state == "ANSWERING"

    def test_answering_to_disconnected(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        r = m.process_event("NETWORK_DISCONNECTED", "E003")
        assert r["status"] == "PROCESSED"
        assert m.state == "DISCONNECTED"

    def test_disconnected_to_answering(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        m.process_event("NETWORK_DISCONNECTED", "E003")
        r = m.process_event("NETWORK_RECONNECTED", "E004")
        assert r["status"] == "PROCESSED"
        assert m.state == "ANSWERING"

    def test_answering_to_submitted(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        r = m.process_event("SUBMIT_EXAM", "E003")
        assert r["status"] == "PROCESSED"
        assert m.state == "SUBMITTED"

    def test_autosave_in_answering(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        r = m.process_event("ANSWER_SAVED", "E003")
        assert r["status"] == "PROCESSED"

    def test_timer_update_in_started(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        r = m.process_event("TIMER_UPDATED", "E002")
        assert r["status"] == "PROCESSED"
        assert m.state == "STARTED"

    def test_submit_from_started(self):
        """Allow submitting directly from STARTED (no answers given)."""
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        r = m.process_event("SUBMIT_EXAM", "E002")
        assert r["status"] == "PROCESSED"
        assert m.state == "SUBMITTED"


class TestInvalidTransitions:
    def test_submit_before_start_is_rejected(self):
        m = new_machine()
        r = m.process_event("SUBMIT_EXAM", "E001")
        assert r["status"] == "REJECTED"
        assert m.state == "IDLE"

    def test_answer_before_start_is_rejected(self):
        m = new_machine()
        r = m.process_event("ANSWER_SUBMITTED", "E001", {"question_id": "Q1", "answer": "A"})
        assert r["status"] == "REJECTED"
        assert m.state == "IDLE"

    def test_start_twice_is_rejected(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        r = m.process_event("START_EXAM", "E002")
        assert r["status"] == "REJECTED"
        assert m.state == "STARTED"

    def test_reconnect_without_disconnect_is_rejected(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        r = m.process_event("NETWORK_RECONNECTED", "E002")
        assert r["status"] == "REJECTED"
        assert m.state == "STARTED"

    def test_event_after_submit_rejected(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("SUBMIT_EXAM", "E002")
        r = m.process_event("ANSWER_SUBMITTED", "E003", {"question_id": "Q1", "answer": "A"})
        assert r["status"] == "REJECTED"
        assert m.state == "SUBMITTED"


# ---------------------------------------------------------------------------
# CATEGORY B — Duplicate / Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_duplicate_event_rejected(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        r1 = m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        state_after_first = m.state
        r2 = m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "B"})
        assert r1["status"] == "PROCESSED"
        assert r2["status"] == "DUPLICATE_REJECTED"
        assert m.state == state_after_first  # state must not change

    def test_duplicate_does_not_increment_processed(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "B"})
        assert m.duplicate_count == 1
        assert len(m.events_processed) == 2  # START_EXAM + first ANSWER

    def test_duplicate_is_recorded_in_rejected(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        rejected_ids = [e["event_id"] for e in m.events_rejected]
        assert "E002" in rejected_ids

    def test_processed_event_ids_consistent(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        # The duplicate must not be added again
        assert m.processed_event_ids.count("E002") == 1 if isinstance(m.processed_event_ids, list) else True
        assert len(m.processed_event_ids) == 2  # E001 and E002

    def test_multiple_duplicates_all_rejected(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        for _ in range(5):
            m.process_event("START_EXAM", "E001")
        assert m.duplicate_count == 5
        assert m.state == "STARTED"


# ---------------------------------------------------------------------------
# CATEGORY C — Delayed Events
# ---------------------------------------------------------------------------

class TestDelayedEvents:
    def test_late_save_after_submit_rejected(self):
        """ANSWER_SAVED arriving after SUBMITTED is a delayed/stale event."""
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        m.process_event("SUBMIT_EXAM", "E003")
        r = m.process_event("ANSWER_SAVED", "E004")
        assert r["status"] == "REJECTED"
        assert m.state == "SUBMITTED"  # must not corrupt state

    def test_reconnect_after_submit_rejected(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("SUBMIT_EXAM", "E002")
        r = m.process_event("NETWORK_RECONNECTED", "E003")
        assert r["status"] == "REJECTED"
        assert m.state == "SUBMITTED"

    def test_delayed_answer_after_submit_does_not_alter_answers(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        m.process_event("SUBMIT_EXAM", "E003")
        answers_before = dict(m.answers)
        m.process_event("ANSWER_SUBMITTED", "E004", {"question_id": "Q1", "answer": "HACKED"})
        assert m.answers == answers_before  # answers unchanged


# ---------------------------------------------------------------------------
# CATEGORY D — Out-of-Order Events
# ---------------------------------------------------------------------------

class TestOutOfOrderEvents:
    def test_answer_before_start(self):
        m = new_machine()
        r = m.process_event("ANSWER_SUBMITTED", "E001", {"question_id": "Q1", "answer": "A"})
        assert r["status"] == "REJECTED"
        assert m.state == "IDLE"

    def test_submit_before_any_event(self):
        m = new_machine()
        r = m.process_event("SUBMIT_EXAM", "E001")
        assert r["status"] == "REJECTED"
        assert m.state == "IDLE"

    def test_disconnect_before_start(self):
        m = new_machine()
        r = m.process_event("NETWORK_DISCONNECTED", "E001")
        assert r["status"] == "REJECTED"
        assert m.state == "IDLE"

    def test_full_out_of_order_sequence(self):
        """Simulate the out-of-order scenario from events.py demo."""
        m = new_machine()
        # Events arrive in wrong order: ANSWER first, then ANSWER again, then START
        r1 = m.process_event("ANSWER_SAVED", "E020", {"question_id": "Q1", "answer": "A"})
        r2 = m.process_event("ANSWER_SUBMITTED", "E021", {"question_id": "Q1", "answer": "A"})
        r3 = m.process_event("START_EXAM", "E022")
        assert r1["status"] == "REJECTED"
        assert r2["status"] == "REJECTED"
        assert r3["status"] == "PROCESSED"
        assert m.state == "STARTED"


# ---------------------------------------------------------------------------
# CATEGORY E — Property-style State Safety
# ---------------------------------------------------------------------------

# Deterministic set of transition sequences covering happy paths
VALID_SEQUENCES = [
    ["START_EXAM", "SUBMIT_EXAM"],
    ["START_EXAM", "ANSWER_SUBMITTED", "SUBMIT_EXAM"],
    ["START_EXAM", "ANSWER_SUBMITTED", "NETWORK_DISCONNECTED", "NETWORK_RECONNECTED", "SUBMIT_EXAM"],
    ["START_EXAM", "TIMER_UPDATED", "ANSWER_SUBMITTED", "ANSWER_SAVED", "SUBMIT_EXAM"],
]

INVALID_OPENINGS = [
    ["SUBMIT_EXAM"],
    ["ANSWER_SUBMITTED"],
    ["NETWORK_DISCONNECTED"],
    ["NETWORK_RECONNECTED"],
    ["ANSWER_SAVED"],
]


class TestPropertyStyleStateSafety:
    @pytest.mark.parametrize("sequence", VALID_SEQUENCES)
    def test_valid_sequence_ends_in_valid_state(self, sequence):
        m = new_machine()
        for i, evt in enumerate(sequence):
            payload = {"question_id": "Q1", "answer": "A"} if "ANSWER" in evt else None
            r = m.process_event(evt, f"EVT{i:03d}", payload)
            assert m.state in VALID_STATES, f"Invalid state after {evt}: {m.state}"
            assert r["status"] == "PROCESSED", f"Expected PROCESSED for {evt}, got {r['status']}"

    @pytest.mark.parametrize("sequence", INVALID_OPENINGS)
    def test_invalid_opening_event_rejected(self, sequence):
        m = new_machine()
        r = m.process_event(sequence[0], "E001")
        assert r["status"] == "REJECTED"
        assert m.state == "IDLE"

    def test_duplicate_event_never_applied_twice(self):
        """Regardless of sequence, a duplicate event_id must never change state twice."""
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "X"})
        state_snap = m.state
        # Send same event many times
        for _ in range(10):
            r = m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "X"})
            assert r["status"] == "DUPLICATE_REJECTED"
            assert m.state == state_snap

    def test_state_always_in_valid_set_under_mixed_sequence(self):
        """Mix of valid and invalid events — state must always be a known value."""
        m = new_machine()
        mixed = [
            ("SUBMIT_EXAM", "E001"),          # invalid from IDLE
            ("START_EXAM", "E002"),            # valid
            ("START_EXAM", "E003"),            # invalid (already STARTED)
            ("ANSWER_SUBMITTED", "E004", {"question_id": "Q1", "answer": "A"}),
            ("NETWORK_DISCONNECTED", "E005"),
            ("SUBMIT_EXAM", "E006"),           # invalid from DISCONNECTED
            ("NETWORK_RECONNECTED", "E007"),
            ("SUBMIT_EXAM", "E008"),
        ]
        for item in mixed:
            evt = item[0]; eid = item[1]
            payload = item[2] if len(item) > 2 else None
            m.process_event(evt, eid, payload)
            assert m.state in VALID_STATES, f"State '{m.state}' not in VALID_STATES after {evt}"

    def test_processed_event_ids_never_shrinks(self):
        """processed_event_ids must only grow, never lose entries."""
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        size_after_1 = len(m.processed_event_ids)
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "A"})
        size_after_2 = len(m.processed_event_ids)
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "B"})  # duplicate
        size_after_dup = len(m.processed_event_ids)
        assert size_after_1 == 1
        assert size_after_2 == 2
        assert size_after_dup == 2  # duplicate does NOT remove existing entries

    def test_answers_not_overwritten_by_duplicate(self):
        m = new_machine()
        m.process_event("START_EXAM", "E001")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "ORIGINAL"})
        original_answer = m.answers.get("Q1")
        m.process_event("ANSWER_SUBMITTED", "E002", {"question_id": "Q1", "answer": "MODIFIED"})
        assert m.answers.get("Q1") == original_answer
