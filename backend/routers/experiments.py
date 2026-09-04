from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import TestCase
from routers.risk import calculate_risk_score
from routers.auth import require_role
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

class ExperimentRequest(BaseModel):
    token: str
    time_budget_minutes: float = 60.0

@router.post("/run")
def run_experiment(req: ExperimentRequest, db: Session = Depends(get_db)):
    # BUG 3 FIX: Enforce tester or higher role
    require_role(req.token, ["tester", "test_lead", "admin"])

    test_cases = db.query(TestCase).filter(TestCase.current_status == "Active").all()

    # Calculate risk scores using real DefectHistory data (Bug 2 fix)
    scored = []
    for tc in test_cases:
        risk = calculate_risk_score(tc, db=db)
        scored.append({
            "test_case_id": tc.test_case_id,
            "name": tc.name,
            "critical_user_journey": tc.critical_user_journey,
            "execution_time_minutes": tc.execution_time_minutes,
            "historical_critical_defect_count": risk["actual_critical_defect_count"],
            "risk_score": risk["risk_score"],
            "priority_category": risk["priority_category"],
        })

    # ============ BASELINE (FIFO order - by test case ID) ============
    baseline_order = sorted(scored, key=lambda x: x["test_case_id"])
    baseline_selected = []
    baseline_time = 0.0
    baseline_critical_defects = 0

    for tc in baseline_order:
        if baseline_time + tc["execution_time_minutes"] <= req.time_budget_minutes:
            baseline_time += tc["execution_time_minutes"]
            baseline_critical_defects += tc["historical_critical_defect_count"]
            baseline_selected.append(tc)

    baseline_cd_per_min = round(baseline_critical_defects / max(baseline_time, 0.1), 4)

    # ============ OPTIMIZED (Risk-based order) ============
    optimized_order = sorted(scored, key=lambda x: x["risk_score"], reverse=True)
    optimized_selected = []
    optimized_time = 0.0
    optimized_critical_defects = 0

    for tc in optimized_order:
        if optimized_time + tc["execution_time_minutes"] <= req.time_budget_minutes:
            optimized_time += tc["execution_time_minutes"]
            optimized_critical_defects += tc["historical_critical_defect_count"]
            optimized_selected.append(tc)

    optimized_cd_per_min = round(optimized_critical_defects / max(optimized_time, 0.1), 4)

    # ============ IMPROVEMENT (Dynamic calculation - Bug 1) ============
    if baseline_cd_per_min > 0:
        improvement_percent = round(((optimized_cd_per_min - baseline_cd_per_min) / baseline_cd_per_min) * 100, 1)
    else:
        improvement_percent = 0.0

    # ============ ERROR ANALYSIS ============
    missed_by_optimizer = []
    all_ids_optimized = set(tc["test_case_id"] for tc in optimized_selected)
    all_ids_baseline = set(tc["test_case_id"] for tc in baseline_selected)

    for tc in scored:
        if tc["test_case_id"] in all_ids_baseline and tc["test_case_id"] not in all_ids_optimized:
            if tc["historical_critical_defect_count"] > 0:
                missed_by_optimizer.append({
                    **tc,
                    "analysis": f"This test has {tc['historical_critical_defect_count']} critical defects but was excluded by the optimizer due to lower risk score ({tc['risk_score']}). This demonstrates a limitation where historical data may not capture emerging risks."
                })

    missed_by_baseline = []
    for tc in scored:
        if tc["test_case_id"] in all_ids_optimized and tc["test_case_id"] not in all_ids_baseline:
            if tc["historical_critical_defect_count"] > 0:
                missed_by_baseline.append({
                    **tc,
                    "analysis": f"This high-risk test ({tc['risk_score']}) with {tc['historical_critical_defect_count']} critical defects was missed by baseline FIFO ordering but caught by the optimizer."
                })

    limitations = [
        {
            "title": "Historical Bias",
            "description": "The optimizer relies on historical defect data. A test case with no past critical defects but a newly introduced risky change may be deprioritized incorrectly."
        },
        {
            "title": "Static Risk Weights",
            "description": "The fixed weight distribution (e.g., business criticality at 25%) may not be optimal for all project phases. Early releases may need higher change-risk weights."
        },
        {
            "title": "Correlated Risks Not Modeled",
            "description": "Network risk and autosave risk are often correlated, but the model treats them independently. A failure in one often implies failure in the other."
        },
    ]

    return {
        "time_budget_minutes": req.time_budget_minutes,
        "total_test_cases": len(scored),
        "baseline": {
            "tests_executed": len(baseline_selected),
            "total_execution_time": round(baseline_time, 1),
            "critical_defects_detected": baseline_critical_defects,
            "cd_per_minute": baseline_cd_per_min,
            "strategy": "FIFO (Sequential test case order)",
            "selected": baseline_selected
        },
        "optimized": {
            "tests_executed": len(optimized_selected),
            "total_execution_time": round(optimized_time, 1),
            "critical_defects_detected": optimized_critical_defects,
            "cd_per_minute": optimized_cd_per_min,
            "strategy": "Risk-based prioritization",
            "selected": optimized_selected
        },
        "improvement": {
            "cd_per_min_improvement_percent": improvement_percent,
            "additional_critical_defects": optimized_critical_defects - baseline_critical_defects,
            "time_saved_minutes": round(baseline_time - optimized_time, 1) if baseline_time > optimized_time else 0,
        },
        "error_analysis": {
            "missed_by_optimizer": missed_by_optimizer,
            "missed_by_baseline": missed_by_baseline,
            "limitations": limitations,
        }
    }
