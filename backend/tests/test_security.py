"""
test_security.py — Category G: RBAC / Ownership Tests

Tests verify:
  G1. Unauthenticated request → 401
  G2. Student accessing tester/admin operation → 403
  G3. Tester accessing admin-only operation → 403
  G4. Test Lead authorized override → 200
  G5. Student cannot modify another student's assessment
  G6. Tester cannot save another student's answer
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

# ---------------------------------------------------------------------------
# G1 — Unauthenticated → 401
# ---------------------------------------------------------------------------

class TestUnauthenticated:
    def test_test_cases_unauthenticated(self, client):
        r = client.get("/api/test-cases/?token=invalid_token_xyz")
        assert r.status_code == 401

    def test_risk_scores_unauthenticated(self, client):
        r = client.get("/api/risk/scores?token=bad_token")
        assert r.status_code == 401

    def test_optimizer_unauthenticated(self, client):
        r = client.post("/api/optimizer/run", json={"token": "invalid", "time_budget_minutes": 60})
        assert r.status_code == 401

    def test_override_unauthenticated(self, client):
        r = client.post("/api/optimizer/override", json={
            "token": "invalid", "test_case_id": "TC001",
            "old_priority": 1, "new_priority": 2, "reason": "test"
        })
        assert r.status_code == 401

    def test_events_unauthenticated(self, client):
        r = client.post("/api/events/simulate", json={
            "token": "invalid", "events": [], "scenario_name": "test"
        })
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# G2 — Student accessing tester/admin operations → 403
# ---------------------------------------------------------------------------

class TestStudentForbidden:
    def test_student_cannot_run_optimizer(self, client, tokens):
        r = client.post("/api/optimizer/run", json={
            "token": tokens["student"], "time_budget_minutes": 60
        })
        assert r.status_code == 403

    def test_student_cannot_access_risk_scores(self, client, tokens):
        r = client.get(f"/api/risk/scores?token={tokens['student']}")
        assert r.status_code == 403

    def test_student_cannot_run_experiments(self, client, tokens):
        r = client.post("/api/experiments/run", json={
            "token": tokens["student"], "time_budget_minutes": 60
        })
        assert r.status_code == 403

    def test_student_cannot_run_event_simulation(self, client, tokens):
        r = client.post("/api/events/simulate", json={
            "token": tokens["student"],
            "events": [{"event_type": "START_EXAM", "event_id": "E001", "sequence_number": 1}],
            "scenario_name": "test"
        })
        assert r.status_code == 403

    def test_student_cannot_override_priority(self, client, tokens):
        r = client.post("/api/optimizer/override", json={
            "token": tokens["student"], "test_case_id": "TC001",
            "old_priority": 1, "new_priority": 2, "reason": "test"
        })
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# G3 — Tester accessing admin-only operations → 403
# ---------------------------------------------------------------------------

class TestTesterForbidden:
    def test_tester_cannot_access_user_management(self, client, tokens):
        r = client.get(f"/api/auth/users?token={tokens['tester']}")
        assert r.status_code == 403

    def test_tester_cannot_override_priority(self, client, tokens):
        r = client.post("/api/optimizer/override", json={
            "token": tokens["tester"], "test_case_id": "TC001",
            "old_priority": 1, "new_priority": 2, "reason": "tester attempt"
        })
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# G4 — Test Lead authorized operations → 200
# ---------------------------------------------------------------------------

class TestLeadAuthorized:
    def test_lead_can_run_optimizer(self, client, tokens):
        r = client.post("/api/optimizer/run", json={
            "token": tokens["test_lead"], "time_budget_minutes": 60
        })
        assert r.status_code == 200

    def test_lead_can_override_priority(self, client, tokens):
        r = client.post("/api/optimizer/override", json={
            "token": tokens["test_lead"], "test_case_id": "TC001",
            "old_priority": 3, "new_priority": 1, "reason": "Lead authorized override"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "Override applied"
        assert data["performed_by"] is not None

    def test_lead_can_access_risk_scores(self, client, tokens):
        r = client.get(f"/api/risk/scores?token={tokens['test_lead']}")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# G5 — Student cannot modify another student's assessment
# ---------------------------------------------------------------------------

class TestAssessmentOwnership:
    def _start_student_submission(self, client, tokens):
        """Create a submission as student user_id=1."""
        r = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        assert r.status_code == 200
        return r.json()["submission_id"]

    def test_student_can_start_own_assessment(self, client, tokens):
        r = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        assert r.status_code in {200}

    def test_student_cannot_start_assessment_for_other_user(self, client, tokens):
        """student1 (user_id=1) tries to start assessment for user_id=2."""
        r = client.post("/api/assessments/start", json={
            "user_id": 2, "assessment_id": 1, "token": tokens["student"]
        })
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# G6 — Tester cannot save another student's answer
# ---------------------------------------------------------------------------

class TestAnswerOwnership:
    def test_tester_cannot_save_student_answer(self, client, tokens):
        """Tester tries to save answer for student's submission → 403."""
        # Start a submission as student
        start_resp = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        assert start_resp.status_code == 200
        sub_id = start_resp.json()["submission_id"]

        # Tester (user_id=2) tries to save answer for student's submission
        r = client.post("/api/assessments/save-answer", json={
            "submission_id": sub_id,
            "question_id": 1,
            "answer": "A",
            "token": tokens["tester"]
        })
        assert r.status_code == 403

    def test_student_can_save_own_answer(self, client, tokens):
        """Student saves answer for their own submission → 200."""
        start_resp = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        assert start_resp.status_code == 200
        sub_id = start_resp.json()["submission_id"]

        r = client.post("/api/assessments/save-answer", json={
            "submission_id": sub_id, "question_id": 1,
            "answer": "A", "token": tokens["student"]
        })
        assert r.status_code == 200

    def test_tester_cannot_submit_student_exam(self, client, tokens):
        """Tester tries to submit student's exam → 403."""
        start_resp = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        sub_id = start_resp.json()["submission_id"]
        r = client.post("/api/assessments/submit", json={
            "submission_id": sub_id, "token": tokens["tester"]
        })
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Admin super-user
# ---------------------------------------------------------------------------

class TestAdminAccess:
    def test_admin_can_list_users(self, client, tokens):
        r = client.get(f"/api/auth/users?token={tokens['admin']}")
        assert r.status_code == 200
        users = r.json()
        assert len(users) > 0

    def test_admin_can_override_priority(self, client, tokens):
        r = client.post("/api/optimizer/override", json={
            "token": tokens["admin"], "test_case_id": "TC004",
            "old_priority": 10, "new_priority": 1, "reason": "Admin override"
        })
        assert r.status_code == 200
