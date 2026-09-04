from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import TestCase, OverrideLog
from routers.risk import calculate_risk_score
from routers.auth import require_role, sessions
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])

class OptimizerRequest(BaseModel):
    time_budget_minutes: float = 60.0
    objective: str = "max_risk"  # max_risk or max_efficiency
    mandatory_only: bool = False
    include_network_test: bool = True
    include_submission_test: bool = True
    include_security_test: bool = True
    prefer_high_risk: bool = True
    prefer_recent_defects: bool = True
    prefer_frequent_journeys: bool = True
    prefer_shorter_execution: bool = False
    prefer_recent_changes: bool = True

class OverrideRequest(BaseModel):
    token: str
    test_case_id: str
    old_priority: int
    new_priority: int
    reason: str

@router.post("/run")
def run_optimizer(req: OptimizerRequest, db: Session = Depends(get_db)):
    test_cases = db.query(TestCase).filter(TestCase.current_status == "Active").all()

    # Calculate risk scores for all test cases
    scored = []
    for tc in test_cases:
        risk = calculate_risk_score(tc)
        scored.append({
            "test_case_id": tc.test_case_id,
            "name": tc.name,
            "module": tc.module,
            "critical_user_journey": tc.critical_user_journey,
            "description": tc.description,
            "execution_time_minutes": tc.execution_time_minutes,
            "is_mandatory": tc.is_mandatory,
            "business_criticality": tc.business_criticality,
            "historical_defect_count": tc.historical_defect_count,
            "historical_critical_defect_count": tc.historical_critical_defect_count,
            "production_usage": tc.production_usage,
            "change_risk": tc.change_risk,
            "network_risk": tc.network_risk,
            "unusual_behaviour_risk": tc.unusual_behaviour_risk,
            **risk
        })

    # Sort by objective
    if req.objective == "max_efficiency":
        scored.sort(key=lambda x: x["efficiency_score"], reverse=True)
    else:
        scored.sort(key=lambda x: x["risk_score"], reverse=True)

    # Apply soft constraint preferences as secondary sorting tiebreakers
    if req.prefer_shorter_execution:
        scored.sort(key=lambda x: (
            -x["risk_score"] if req.objective == "max_risk" else -x["efficiency_score"],
            x["execution_time_minutes"]
        ))

    # === HARD CONSTRAINTS ===
    hard_constraint_violations = []

    # 1. Mandatory tests must be included
    mandatory_ids = [s["test_case_id"] for s in scored if s["is_mandatory"]]

    # 2. Must include at least one network recovery test
    network_tests = [s for s in scored if "network" in s["critical_user_journey"].lower() or "network" in s["module"].lower()]

    # 3. Must include critical submission testing
    submission_tests = [s for s in scored if "submit" in s["critical_user_journey"].lower() or "submission" in s["module"].lower()]

    # 4. Security-critical tests cannot be excluded
    security_tests = [s for s in scored if "security" in s["module"].lower() or "access control" in s["critical_user_journey"].lower()]

    # === PORTFOLIO SELECTION ===
    selected = []
    deferred = []
    excluded = []
    total_time = 0.0

    # First pass: collect mandatory and hard-constraint test IDs
    must_include_ids = set(mandatory_ids)
    if req.include_network_test and network_tests:
        must_include_ids.add(network_tests[0]["test_case_id"])
    if req.include_submission_test and submission_tests:
        must_include_ids.add(submission_tests[0]["test_case_id"])
    if req.include_security_test and security_tests:
        must_include_ids.add(security_tests[0]["test_case_id"])

    # --- HARD CONSTRAINT: mandatory tests must not exceed time budget ---
    mandatory_total_time = sum(
        s["execution_time_minutes"] for s in scored if s["test_case_id"] in must_include_ids
    )

    if mandatory_total_time > req.time_budget_minutes:
        # Return UNFEASIBLE — do NOT return an over-budget portfolio
        return {
            "status": "UNFEASIBLE",
            "objective": req.objective,
            "objective_label": "Maximum Risk Coverage" if req.objective == "max_risk" else "Maximum Risk per Minute",
            "time_budget_minutes": req.time_budget_minutes,
            "mandatory_execution_time_required": round(mandatory_total_time, 1),
            "shortfall_minutes": round(mandatory_total_time - req.time_budget_minutes, 1),
            "reason": (
                f"Cannot satisfy constraints: mandatory tests require {mandatory_total_time:.1f} min "
                f"but budget is only {req.time_budget_minutes:.1f} min. "
                f"Please increase the time budget to at least {mandatory_total_time:.1f} min."
            ),
            "total_test_cases": len(scored),
            "selected_count": 0,
            "deferred_count": len(scored),
            "excluded_count": 0,
            "total_execution_time": 0.0,
            "risk_coverage_percent": 0.0,
            "critical_defect_coverage_percent": 0.0,
            "hard_constraint_violations": [
                f"UNFEASIBLE: Mandatory tests require {mandatory_total_time:.1f} min, exceeding budget of {req.time_budget_minutes:.1f} min."
            ],
            "soft_constraints": [],
            "selected": [],
            "deferred": scored,
            "excluded": [],
        }

    # Add mandatory tests first (fits within budget, verified above)
    for s in scored:
        if s["test_case_id"] in must_include_ids:
            total_time += s["execution_time_minutes"]
            selected.append(s)

    # Check remaining capacity warning (should not occur since we verified above)
    if total_time > req.time_budget_minutes:
        hard_constraint_violations.append(
            f"WARNING: Mandatory tests alone require {total_time:.1f} min, exceeding budget of {req.time_budget_minutes:.1f} min. Cannot satisfy all hard constraints."
        )

    # Second pass: add remaining tests within budget
    for s in scored:
        if s["test_case_id"] not in must_include_ids:
            if total_time + s["execution_time_minutes"] <= req.time_budget_minutes:
                total_time += s["execution_time_minutes"]
                selected.append(s)
            else:
                deferred.append(s)

    # Assign priorities
    for i, s in enumerate(selected):
        s["priority"] = i + 1

    for i, s in enumerate(deferred):
        s["priority"] = len(selected) + i + 1

    # Excluded = those that don't meet minimum criteria (none in this version)
    # All deferred are potential execution candidates if more time becomes available

    # === SOFT CONSTRAINTS EVALUATION ===
    soft_constraints = []
    if req.prefer_high_risk:
        high_risk_selected = sum(1 for s in selected if s["risk_score"] >= 7.0)
        high_risk_total = sum(1 for s in scored if s["risk_score"] >= 7.0)
        soft_constraints.append({
            "constraint": "Prefer high-risk tests",
            "satisfied": high_risk_selected >= high_risk_total * 0.7,
            "detail": f"{high_risk_selected}/{high_risk_total} high-risk tests selected"
        })

    if req.prefer_recent_defects:
        defect_selected = sum(1 for s in selected if s["historical_critical_defect_count"] >= 3)
        defect_total = sum(1 for s in scored if s["historical_critical_defect_count"] >= 3)
        soft_constraints.append({
            "constraint": "Prefer tests with recent critical defects",
            "satisfied": defect_selected >= defect_total * 0.6,
            "detail": f"{defect_selected}/{defect_total} high-defect tests selected"
        })

    if req.prefer_frequent_journeys:
        frequent_selected = sum(1 for s in selected if s["production_usage"] >= 8.0)
        frequent_total = sum(1 for s in scored if s["production_usage"] >= 8.0)
        soft_constraints.append({
            "constraint": "Prefer frequently used journeys",
            "satisfied": frequent_selected >= frequent_total * 0.6,
            "detail": f"{frequent_selected}/{frequent_total} high-usage tests selected"
        })

    if req.prefer_shorter_execution:
        avg_time_selected = sum(s["execution_time_minutes"] for s in selected) / max(len(selected), 1)
        avg_time_all = sum(s["execution_time_minutes"] for s in scored) / max(len(scored), 1)
        soft_constraints.append({
            "constraint": "Prefer shorter execution times",
            "satisfied": avg_time_selected <= avg_time_all,
            "detail": f"Avg selected: {avg_time_selected:.1f} min vs overall avg: {avg_time_all:.1f} min"
        })

    if req.prefer_recent_changes:
        change_selected = sum(1 for s in selected if s["change_risk"] >= 6.0)
        change_total = sum(1 for s in scored if s["change_risk"] >= 6.0)
        soft_constraints.append({
            "constraint": "Prefer recently changed modules",
            "satisfied": change_selected >= change_total * 0.5,
            "detail": f"{change_selected}/{change_total} high-change-risk tests selected"
        })

    # === COVERAGE METRICS ===
    total_risk = sum(s["risk_score"] for s in scored)
    selected_risk = sum(s["risk_score"] for s in selected)
    total_critical_defects = sum(s["historical_critical_defect_count"] for s in scored)
    selected_critical_defects = sum(s["historical_critical_defect_count"] for s in selected)

    return {
        "objective": req.objective,
        "objective_label": "Maximum Risk Coverage" if req.objective == "max_risk" else "Maximum Risk per Minute",
        "time_budget_minutes": req.time_budget_minutes,
        "total_execution_time": round(total_time, 1),
        "total_test_cases": len(scored),
        "selected_count": len(selected),
        "deferred_count": len(deferred),
        "excluded_count": len(excluded),
        "risk_coverage_percent": round(selected_risk / max(total_risk, 1) * 100, 1),
        "critical_defect_coverage_percent": round(selected_critical_defects / max(total_critical_defects, 1) * 100, 1),
        "hard_constraint_violations": hard_constraint_violations,
        "soft_constraints": soft_constraints,
        "selected": selected,
        "deferred": deferred,
        "excluded": excluded,
    }

@router.post("/override")
def override_priority(req: OverrideRequest, db: Session = Depends(get_db)):
    # Verify authorization
    user = require_role(req.token, ["test_lead", "admin"])

    # Create audit log
    override = OverrideLog(
        test_case_id=req.test_case_id,
        old_priority=req.old_priority,
        new_priority=req.new_priority,
        reason=req.reason,
        performed_by=user["full_name"],
        role=user["role"],
    )
    db.add(override)
    db.commit()

    return {
        "status": "Override applied",
        "test_case_id": req.test_case_id,
        "old_priority": req.old_priority,
        "new_priority": req.new_priority,
        "reason": req.reason,
        "performed_by": user["full_name"],
        "role": user["role"],
        "timestamp": str(override.timestamp),
    }

@router.get("/overrides")
def get_overrides(db: Session = Depends(get_db)):
    overrides = db.query(OverrideLog).order_by(OverrideLog.timestamp.desc()).all()
    return [{
        "id": o.id, "test_case_id": o.test_case_id,
        "old_priority": o.old_priority, "new_priority": o.new_priority,
        "reason": o.reason, "performed_by": o.performed_by,
        "role": o.role, "timestamp": str(o.timestamp)
    } for o in overrides]
