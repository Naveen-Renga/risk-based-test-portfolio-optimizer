from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import TestCase, DefectHistory
from routers.auth import require_role

router = APIRouter(prefix="/api/test-cases", tags=["test_cases"])

# BUG 3 FIX: Require tester or higher role for test case & defect endpoints

@router.get("/")
def get_test_cases(token: str, db: Session = Depends(get_db)):
    require_role(token, ["tester", "test_lead", "admin"])
    tcs = db.query(TestCase).all()
    return [{
        "id": tc.id, "test_case_id": tc.test_case_id, "name": tc.name,
        "module": tc.module, "critical_user_journey": tc.critical_user_journey,
        "description": tc.description, "business_criticality": tc.business_criticality,
        "historical_defect_count": tc.historical_defect_count,
        "historical_critical_defect_count": tc.historical_critical_defect_count,
        "production_usage": tc.production_usage, "change_risk": tc.change_risk,
        "network_risk": tc.network_risk, "unusual_behaviour_risk": tc.unusual_behaviour_risk,
        "execution_time_minutes": tc.execution_time_minutes,
        "is_mandatory": tc.is_mandatory, "current_status": tc.current_status,
    } for tc in tcs]

@router.get("/{test_case_id}")
def get_test_case(test_case_id: str, token: str, db: Session = Depends(get_db)):
    require_role(token, ["tester", "test_lead", "admin"])
    tc = db.query(TestCase).filter(TestCase.test_case_id == test_case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    return {
        "id": tc.id, "test_case_id": tc.test_case_id, "name": tc.name,
        "module": tc.module, "critical_user_journey": tc.critical_user_journey,
        "description": tc.description, "business_criticality": tc.business_criticality,
        "historical_defect_count": tc.historical_defect_count,
        "historical_critical_defect_count": tc.historical_critical_defect_count,
        "production_usage": tc.production_usage, "change_risk": tc.change_risk,
        "network_risk": tc.network_risk, "unusual_behaviour_risk": tc.unusual_behaviour_risk,
        "execution_time_minutes": tc.execution_time_minutes,
        "is_mandatory": tc.is_mandatory, "current_status": tc.current_status,
    }

@router.get("/defects/history")
def get_defect_history(token: str, db: Session = Depends(get_db)):
    require_role(token, ["tester", "test_lead", "admin"])
    defects = db.query(DefectHistory).all()
    return [{
        "id": d.id, "test_case_id": d.test_case_id, "defect_id": d.defect_id,
        "severity": d.severity, "module": d.module, "description": d.description,
        "detected_date": d.detected_date, "resolved": d.resolved,
        "resolution_time_hours": d.resolution_time_hours
    } for d in defects]

@router.get("/defects/summary")
def get_defect_summary(token: str, db: Session = Depends(get_db)):
    require_role(token, ["tester", "test_lead", "admin"])
    defects = db.query(DefectHistory).all()
    by_severity = {}
    by_module = {}
    for d in defects:
        by_severity[d.severity] = by_severity.get(d.severity, 0) + 1
        by_module[d.module] = by_module.get(d.module, 0) + 1

    return {
        "total_defects": len(defects),
        "by_severity": by_severity,
        "by_module": by_module,
        "unresolved": sum(1 for d in defects if not d.resolved)
    }
