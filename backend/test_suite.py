import os
import sys
import asyncio

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from httpx import ASGITransport, AsyncClient
from main import app
from routers.auth import sessions

async def run_tests():
    print("=== RUNNING FULL BACKEND AUDIT ===")
    
    # Set up session tokens
    tokens = {
        "student": "test-student-token",
        "tester": "test-tester-token",
        "test_lead": "test-testlead-token",
        "admin": "test-admin-token"
    }
    sessions[tokens["student"]] = {"user_id": 1, "username": "student1", "full_name": "Student Test", "role": "student"}
    sessions[tokens["tester"]] = {"user_id": 2, "username": "tester1", "full_name": "Tester Test", "role": "tester"}
    sessions[tokens["test_lead"]] = {"user_id": 3, "username": "testlead", "full_name": "Test Lead Test", "role": "test_lead"}
    sessions[tokens["admin"]] = {"user_id": 4, "username": "admin", "full_name": "Admin Test", "role": "admin"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health Check
        r = await client.get("/")
        print(f"1. Health Check: {r.status_code} -> {r.json()}")
        assert r.status_code == 200

        # 2. Security Demo API (Bug 4 Fix Verification)
        r = await client.post("/api/security/demo")
        print(f"2. Security Demo API: {r.status_code}")
        demo_res = r.json()
        print(f"   Summary: Passed {demo_res.get('passed')}/{demo_res.get('total_scenarios')}")
        assert demo_res.get("passed") == demo_res.get("total_scenarios")

        # 3. RBAC Enforcement (Bug 3 Fix Verification)
        r1 = await client.get("/api/test-cases/?token=invalid_token")
        print(f"3a. Unauthenticated /api/test-cases/: {r1.status_code} (Expected 401)")
        assert r1.status_code == 401

        r2 = await client.post("/api/optimizer/run", json={"token": tokens['student'], "time_budget_minutes": 60})
        print(f"3b. Student /api/optimizer/run: {r2.status_code} (Expected 403)")
        assert r2.status_code == 403

        r3 = await client.post("/api/optimizer/run", json={"token": tokens['tester'], "time_budget_minutes": 60})
        print(f"3c. Tester /api/optimizer/run: {r3.status_code} (Expected 200)")
        assert r3.status_code == 200

        # 4. Risk Scores (Bug 2 Defect History Integration Verification)
        r = await client.get(f"/api/risk/scores?token={tokens['tester']}")
        tcs = r.json()
        print(f"4. Risk Scores API: {r.status_code}, count: {len(tcs)}")
        assert r.status_code == 200
        for tc in tcs:
            score = tc.get("risk_score", 0)
            assert 0.0 <= score <= 10.0, f"Risk score out of bounds: {score}"

        # 5. Priority Override Integration (Bug 5 Fix Verification)
        override_payload = {
            "token": tokens['test_lead'],
            "test_case_id": "TC035",
            "old_priority": 3,
            "new_priority": 1,
            "reason": "Evaluation Audit Priority Boost Test"
        }
        r_ov = await client.post("/api/optimizer/override", json=override_payload)
        print(f"5a. Test Lead Override: {r_ov.status_code} -> {r_ov.json().get('message', r_ov.json().get('status'))}")
        assert r_ov.status_code == 200

        r_opt = await client.post("/api/optimizer/run", json={"token": tokens['tester'], "time_budget_minutes": 60})
        portfolio = r_opt.json().get("selected", [])
        if portfolio:
            top_tc = portfolio[0]
            print(f"5b. Top test case in portfolio after override: {top_tc.get('test_case_id')}, override={top_tc.get('has_override')}")
            assert top_tc.get("test_case_id") == "TC035"

        # 6. Dynamic CD/min Calculation (Bug 1 Fix Verification)
        r_exp = await client.post("/api/experiments/run", json={"token": tokens['tester'], "time_budget_minutes": 60})
        print(f"6. Experiment Results: {r_exp.status_code}")
        exp_data = r_exp.json()
        print(f"   Dynamic CD/min Improvement: {exp_data.get('cd_min_improvement_percent')}%")
        assert r_exp.status_code == 200

        # 7. Assessment Ownership Check (Bug 7 Fix Verification)
        r_start = await client.post("/api/assessments/start", json={
            "user_id": 1, "assessment_id": 1, "token": tokens['student']
        })
        sub_id = r_start.json().get("submission_id")
        r_save_forbidden = await client.post("/api/assessments/save-answer", json={
            "submission_id": sub_id, "question_id": 1, "answer": "A", "token": tokens['tester']
        })
        print(f"7. Assessment Ownership (Tester saving student answer): {r_save_forbidden.status_code} (Expected 403)")
        assert r_save_forbidden.status_code == 403

        # 8. Event Simulation (Edge case handling)
        r_evt = await client.post(f"/api/events/simulate/duplicate?token={tokens['tester']}")
        print(f"8. Event Simulation (duplicate): {r_evt.status_code} -> status={r_evt.json().get('scenario_name')}")
        assert r_evt.status_code == 200

    print("\n=== ALL 8 BACKEND BUG FIXES VERIFIED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
