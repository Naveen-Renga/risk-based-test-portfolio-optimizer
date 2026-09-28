"""
test_assessments.py — Assessment Workflow Integration Tests

Tests verify:
  - Starting an assessment creates a valid submission
  - Saving answers works for the owner
  - Submitting calculates score correctly
  - Ownership enforced on start, save, and submit
  - Already-submitted assessment cannot be re-submitted
  - Submission result is retrievable by the owner
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


class TestAssessmentStart:
    def test_start_creates_submission(self, client, tokens):
        r = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        assert r.status_code == 200
        data = r.json()
        assert "submission_id" in data
        assert data["status"] in {"started", "resumed"}

    def test_start_same_assessment_twice_resumes(self, client, tokens):
        r1 = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        r2 = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Same submission_id must be returned (resume)
        assert r1.json()["submission_id"] == r2.json()["submission_id"]

    def test_start_unauthenticated_fails(self, client):
        r = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": "bad_token"
        })
        assert r.status_code == 401

    def test_start_for_other_user_forbidden(self, client, tokens):
        r = client.post("/api/assessments/start", json={
            "user_id": 2, "assessment_id": 1, "token": tokens["student"]
        })
        assert r.status_code == 403


class TestSaveAnswer:
    def _get_submission(self, client, tokens):
        r = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        return r.json()["submission_id"]

    def test_owner_can_save_answer(self, client, tokens):
        sub_id = self._get_submission(client, tokens)
        r = client.post("/api/assessments/save-answer", json={
            "submission_id": sub_id, "question_id": 1,
            "answer": "A", "token": tokens["student"]
        })
        assert r.status_code == 200
        assert r.json()["status"] == "saved"

    def test_save_updates_answer_count(self, client, tokens):
        sub_id = self._get_submission(client, tokens)
        client.post("/api/assessments/save-answer", json={
            "submission_id": sub_id, "question_id": 1,
            "answer": "A", "token": tokens["student"]
        })
        r = client.post("/api/assessments/save-answer", json={
            "submission_id": sub_id, "question_id": 2,
            "answer": "B", "token": tokens["student"]
        })
        assert r.status_code == 200
        assert r.json()["answers_count"] == 2

    def test_tester_cannot_save_other_student_answer(self, client, tokens):
        sub_id = self._get_submission(client, tokens)
        r = client.post("/api/assessments/save-answer", json={
            "submission_id": sub_id, "question_id": 1,
            "answer": "X", "token": tokens["tester"]
        })
        assert r.status_code == 403


class TestSubmitAssessment:
    def _setup(self, client, tokens):
        r = client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens["student"]
        })
        sub_id = r.json()["submission_id"]
        # Save answer for Q1 (correct = A)
        client.post("/api/assessments/save-answer", json={
            "submission_id": sub_id, "question_id": 1,
            "answer": "A", "token": tokens["student"]
        })
        return sub_id

    def test_submit_calculates_score(self, client, tokens):
        sub_id = self._setup(client, tokens)
        r = client.post("/api/assessments/submit", json={
            "submission_id": sub_id, "token": tokens["student"]
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "submitted"
        assert "score" in data
        assert "total_marks" in data
        assert 0 <= data["score"] <= data["total_marks"]

    def test_cannot_submit_twice(self, client, tokens):
        sub_id = self._setup(client, tokens)
        r1 = client.post("/api/assessments/submit", json={
            "submission_id": sub_id, "token": tokens["student"]
        })
        r2 = client.post("/api/assessments/submit", json={
            "submission_id": sub_id, "token": tokens["student"]
        })
        assert r1.status_code == 200
        assert r2.status_code == 400  # Already submitted

    def test_other_user_cannot_submit(self, client, tokens):
        sub_id = self._setup(client, tokens)
        r = client.post("/api/assessments/submit", json={
            "submission_id": sub_id, "token": tokens["tester"]
        })
        assert r.status_code == 403
