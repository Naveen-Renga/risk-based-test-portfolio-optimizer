from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import SecurityLog
from routers.auth import sessions
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/security", tags=["security"])

class SecurityCheckRequest(BaseModel):
    token: str
    action: str  # portfolio_override, admin_config, optimizer_access, test_lead_action

# Role-action permissions map
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
            result="DENIED", reason="Invalid or expired session token"
        )
        db.add(log)
        db.commit()
        return {
            "result": "DENIED",
            "reason": "Invalid or expired session token",
            "action": req.action
        }

    allowed_roles = PERMISSIONS.get(req.action, [])
    is_allowed = user["role"] in allowed_roles

    log = SecurityLog(
        action=req.action, user=user["full_name"], role=user["role"],
        result="ALLOWED" if is_allowed else "DENIED",
        reason=f"Role '{user['role']}' {'has' if is_allowed else 'does not have'} permission for '{req.action}'. Required: {', '.join(allowed_roles)}"
    )
    db.add(log)
    db.commit()

    return {
        "result": "ALLOWED" if is_allowed else "DENIED",
        "user": user["full_name"],
        "role": user["role"],
        "action": req.action,
        "required_roles": allowed_roles,
        "reason": log.reason
    }

@router.post("/demo")
def run_security_demo(db: Session = Depends(get_db)):
    """Run all security demo scenarios and return results."""
    scenarios = [
        {"role": "student", "action": "portfolio_override", "expected": "DENIED"},
        {"role": "tester", "action": "portfolio_override", "expected": "DENIED"},
        {"role": "test_lead", "action": "portfolio_override", "expected": "ALLOWED"},
        {"role": "admin", "action": "portfolio_override", "expected": "ALLOWED"},
        {"role": "student", "action": "optimizer_access", "expected": "DENIED"},
        {"role": "tester", "action": "optimizer_access", "expected": "ALLOWED"},
        {"role": "student", "action": "admin_config", "expected": "DENIED"},
        {"role": "tester", "action": "admin_config", "expected": "DENIED"},
        {"role": "admin", "action": "admin_config", "expected": "ALLOWED"},
        {"role": "test_lead", "action": "test_lead_action", "expected": "ALLOWED"},
        {"role": "tester", "action": "test_lead_action", "expected": "DENIED"},
    ]

    results = []
    for s in scenarios:
        allowed_roles = PERMISSIONS.get(s["action"], [])
        is_allowed = s["role"] in allowed_roles
        actual = "ALLOWED" if is_allowed else "DENIED"
        passed = actual == s["expected"]

        log = SecurityLog(
            action=s["action"], user=f"Demo {s['role']}", role=s["role"],
            result=actual, reason=f"Security demo: {s['role']} attempted {s['action']}"
        )
        db.add(log)

        results.append({
            **s,
            "actual": actual,
            "passed": passed,
            "required_roles": allowed_roles,
        })

    db.commit()

    return {
        "total_scenarios": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "results": results
    }

@router.get("/logs")
def get_security_logs(db: Session = Depends(get_db)):
    logs = db.query(SecurityLog).order_by(SecurityLog.timestamp.desc()).limit(50).all()
    return [{
        "id": l.id, "action": l.action, "user": l.user,
        "role": l.role, "result": l.result, "reason": l.reason,
        "timestamp": str(l.timestamp)
    } for l in logs]

@router.get("/permissions")
def get_permissions():
    return PERMISSIONS
