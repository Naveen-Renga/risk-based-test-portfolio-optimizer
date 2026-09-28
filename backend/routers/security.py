from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import SecurityLog, User
from routers.auth import sessions, hash_password
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/security", tags=["security"])

class SecurityCheckRequest(BaseModel):
    token: str
    action: str  # portfolio_override, admin_config, optimizer_access, test_lead_action

PERMISSIONS = {
    "portfolio_override": ["test_lead", "admin"],
    "admin_config": ["admin"],
    "optimizer_access": ["tester", "test_lead", "admin"],
    "test_lead_action": ["test_lead", "admin"],
    "view_test_cases": ["tester", "test_lead", "admin"],
    "student_assessment": ["student", "admin"],
}

@router.post("/check")
def check_access(req: SecurityCheckRequest, db: Session = Depends(get_db)):
    user = sessions.get(req.token)
    if not user:
        log = SecurityLog(
            action=req.action, user="Unknown", role="Unknown",
            result="DENIED", reason="401 Unauthorized - Invalid or expired session token"
        )
        db.add(log)
        db.commit()
        return {
            "result": "DENIED",
            "http_status": 401,
            "reason": "Invalid or expired session token",
            "action": req.action
        }

    allowed_roles = PERMISSIONS.get(req.action, [])
    is_allowed = user["role"] in allowed_roles
    http_status = 200 if is_allowed else 403

    log = SecurityLog(
        action=req.action, user=user["full_name"], role=user["role"],
        result="ALLOWED" if is_allowed else "DENIED",
        reason=f"HTTP {http_status}: Role '{user['role']}' {'has' if is_allowed else 'does not have'} permission for '{req.action}'. Required: {', '.join(allowed_roles)}"
    )
    db.add(log)
    db.commit()

    return {
        "result": "ALLOWED" if is_allowed else "DENIED",
        "http_status": http_status,
        "user": user["full_name"],
        "role": user["role"],
        "action": req.action,
        "required_roles": allowed_roles,
        "reason": log.reason
    }

async def _execute_security_demo_async():
    from main import app
    from httpx import ASGITransport, AsyncClient

    # Set up temporary demo session tokens
    tokens = {
        "student": "demo-token-student-uuid",
        "tester": "demo-token-tester-uuid",
        "test_lead": "demo-token-testlead-uuid",
        "admin": "demo-token-admin-uuid",
    }
    sessions[tokens["student"]] = {"user_id": 1, "username": "student1", "full_name": "Student Demo", "role": "student"}
    sessions[tokens["tester"]] = {"user_id": 2, "username": "tester1", "full_name": "Tester Demo", "role": "tester"}
    sessions[tokens["test_lead"]] = {"user_id": 3, "username": "testlead", "full_name": "Test Lead Demo", "role": "test_lead"}
    sessions[tokens["admin"]] = {"user_id": 4, "username": "admin", "full_name": "Admin Demo", "role": "admin"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        scenarios = [
            {
                "role": "unauthenticated",
                "endpoint": "GET /api/test-cases/?token=invalid_token",
                "test_type": "Unauthenticated access",
                "expected_status": 401,
                "call": lambda: client.get("/api/test-cases/?token=invalid_token")
            },
            {
                "role": "student",
                "endpoint": "POST /api/optimizer/run",
                "test_type": "Student attempts tester/admin optimizer endpoint",
                "expected_status": 403,
                "call": lambda: client.post("/api/optimizer/run", json={"token": tokens["student"], "time_budget_minutes": 60})
            },
            {
                "role": "student",
                "endpoint": "POST /api/optimizer/override",
                "test_type": "Student attempts priority override",
                "expected_status": 403,
                "call": lambda: client.post("/api/optimizer/override", json={"token": tokens["student"], "test_case_id": "TC001", "old_priority": 1, "new_priority": 2, "reason": "test"})
            },
            {
                "role": "tester",
                "endpoint": "GET /api/auth/users",
                "test_type": "Tester attempts admin-only user management",
                "expected_status": 403,
                "call": lambda: client.get(f"/api/auth/users?token={tokens['tester']}")
            },
            {
                "role": "tester",
                "endpoint": "POST /api/optimizer/override",
                "test_type": "Tester attempts priority override (Lead/Admin required)",
                "expected_status": 403,
                "call": lambda: client.post("/api/optimizer/override", json={"token": tokens["tester"], "test_case_id": "TC001", "old_priority": 1, "new_priority": 2, "reason": "test"})
            },
            {
                "role": "tester",
                "endpoint": "POST /api/optimizer/run",
                "test_type": "Tester accesses portfolio optimizer",
                "expected_status": 200,
                "call": lambda: client.post("/api/optimizer/run", json={"token": tokens["tester"], "time_budget_minutes": 60})
            },
            {
                "role": "test_lead",
                "endpoint": "POST /api/optimizer/override",
                "test_type": "Test Lead executes authorized priority override",
                "expected_status": 200,
                "call": lambda: client.post("/api/optimizer/override", json={"token": tokens["test_lead"], "test_case_id": "TC001", "old_priority": 5, "new_priority": 1, "reason": "Urgent Lead Override"})
            },
            {
                "role": "admin",
                "endpoint": "GET /api/auth/users",
                "test_type": "Admin accesses user management endpoint",
                "expected_status": 200,
                "call": lambda: client.get(f"/api/auth/users?token={tokens['admin']}")
            },
        ]

        results = []
        for s in scenarios:
            res = await s["call"]()
            actual_status = res.status_code
            passed = actual_status == s["expected_status"]

            result_str = "ALLOWED (200 OK)" if actual_status == 200 else f"DENIED (HTTP {actual_status})"
            expected_str = "ALLOWED (200 OK)" if s["expected_status"] == 200 else f"DENIED (HTTP {s['expected_status']})"

            results.append({
                "role": s["role"],
                "test_type": s["test_type"],
                "endpoint": s["endpoint"],
                "expected_status": s["expected_status"],
                "actual_status": actual_status,
                "expected": expected_str,
                "actual": result_str,
                "passed": passed,
            })

    return results

@router.post("/demo")
def run_security_demo(db: Session = Depends(get_db)):
    """
    BUG 4 FIX: Performs REAL authorization tests against actual backend endpoints
    using httpx.AsyncClient + ASGITransport. Returns exact HTTP status codes (200, 401, 403).
    """
    results = asyncio.run(_execute_security_demo_async())

    for r in results:
        log = SecurityLog(
            action=r["test_type"],
            user=f"Demo {r['role']}",
            role=r["role"],
            result="ALLOWED" if r["actual_status"] == 200 else "DENIED",
            reason=f"Real HTTP Subrequest to {r['endpoint']} -> returned HTTP {r['actual_status']} (Expected HTTP {r['expected_status']})"
        )
        db.add(log)

    db.commit()

    return {
        "total_scenarios": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "results": results
    }

@router.get("/logs")
def get_security_logs(token: str, db: Session = Depends(get_db)):
    from routers.auth import require_role
    require_role(token, ["tester", "test_lead", "admin"])
    logs = db.query(SecurityLog).order_by(SecurityLog.timestamp.desc()).limit(50).all()
    return [{
        "id": l.id, "action": l.action, "user": l.user,
        "role": l.role, "result": l.result, "reason": l.reason,
        "timestamp": str(l.timestamp)
    } for l in logs]

@router.get("/permissions")
def get_permissions():
    return PERMISSIONS
