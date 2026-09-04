from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import TestCase, DefectHistory
from routers.auth import sessions

router = APIRouter(prefix="/api/risk", tags=["risk"])

WEIGHTS = {
    "business_criticality": 0.25,
    "historical_defect_risk": 0.20,
    "change_risk": 0.20,
    "production_usage": 0.15,
    "network_risk": 0.10,
    "unusual_behaviour_risk": 0.10,
}


def get_historical_critical_defect_count(tc_id: str, db: Session) -> int:
    """
    BUG 2 FIX: Count actual Critical-severity defects from the DefectHistory
    table instead of using the stale TestCase.historical_critical_defect_count
    seed field. This makes Risk Analysis and Defect History consistent.
    """
    return (
        db.query(DefectHistory)
        .filter(
            DefectHistory.test_case_id == tc_id,
            DefectHistory.severity == "Critical",
        )
        .count()
    )


def calculate_risk_score(tc, db: Session = None, actual_critical_count: int = None):
    """Calculate risk score using the weighted formula.

    If db is provided, historical_defect_risk is derived from the
    DefectHistory table (single source of truth).
    If actual_critical_count is supplied directly it is used as-is (for
    callers that have already fetched the count to avoid redundant queries).
    Falls back to tc.historical_critical_defect_count only when neither is
    available (rare backwards-compat path).
    """
    if actual_critical_count is None:
        if db is not None:
            actual_critical_count = get_historical_critical_defect_count(tc.test_case_id, db)
        else:
            # Fallback: use seed field (should not occur in normal flow)
            actual_critical_count = tc.historical_critical_defect_count

    # Normalize historical defect risk to 0-10 scale
    # max_defects = 25 based on seed data; scale relative to 30% of that
    max_defects = 25
    defect_risk = min((actual_critical_count / max(max_defects * 0.3, 1)) * 10, 10)

    components = {
        "business_criticality": {"value": tc.business_criticality, "weight": WEIGHTS["business_criticality"]},
        "historical_defect_risk": {"value": round(defect_risk, 2), "weight": WEIGHTS["historical_defect_risk"]},
        "change_risk": {"value": tc.change_risk, "weight": WEIGHTS["change_risk"]},
        "production_usage": {"value": tc.production_usage, "weight": WEIGHTS["production_usage"]},
        "network_risk": {"value": tc.network_risk, "weight": WEIGHTS["network_risk"]},
        "unusual_behaviour_risk": {"value": tc.unusual_behaviour_risk, "weight": WEIGHTS["unusual_behaviour_risk"]},
    }

    risk_score = sum(c["value"] * c["weight"] for c in components.values())
    risk_score = round(min(risk_score, 10), 2)

    # Priority category
    if risk_score >= 8.0:
        priority_category = "Critical"
    elif risk_score >= 6.0:
        priority_category = "High"
    elif risk_score >= 4.0:
        priority_category = "Medium"
    else:
        priority_category = "Low"

    # Reason
    top_factors = sorted(components.items(), key=lambda x: x[1]["value"] * x[1]["weight"], reverse=True)
    reasons = []
    for name, comp in top_factors[:3]:
        label = name.replace("_", " ").title()
        reasons.append(f"{label}: {comp['value']}")

    return {
        "risk_score": risk_score,
        "priority_category": priority_category,
        "components": components,
        "reason": "; ".join(reasons),
        "efficiency_score": round(risk_score / max(tc.execution_time_minutes, 0.1), 2),
        # Expose the actual defect count used so the UI can show it
        "actual_critical_defect_count": actual_critical_count,
    }


# ---------------------------------------------------------------------------
# BUG 3 FIX: All risk endpoints require tester (or higher) role.
# ---------------------------------------------------------------------------

def _require_tester(token: str):
    """Dependency helper — raises 401/403 for unauthenticated or low-role."""
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = sessions[token]
    if user["role"] not in ["tester", "test_lead", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied: Tester role or above required")
    return user


@router.get("/scores")
def get_risk_scores(token: str, db: Session = Depends(get_db)):
    _require_tester(token)
    test_cases = db.query(TestCase).all()
    results = []
    for tc in test_cases:
        risk = calculate_risk_score(tc, db=db)
        results.append({
            "test_case_id": tc.test_case_id,
            "name": tc.name,
            "module": tc.module,
            "critical_user_journey": tc.critical_user_journey,
            "execution_time_minutes": tc.execution_time_minutes,
            "is_mandatory": tc.is_mandatory,
            **risk,
        })
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


@router.get("/weights")
def get_weights(token: str):
    _require_tester(token)
    return WEIGHTS


@router.get("/distribution")
def get_risk_distribution(token: str, db: Session = Depends(get_db)):
    _require_tester(token)
    test_cases = db.query(TestCase).all()
    distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for tc in test_cases:
        risk = calculate_risk_score(tc, db=db)
        distribution[risk["priority_category"]] += 1
    return distribution


@router.get("/formula")
def get_formula(token: str):
    _require_tester(token)
    return {
        "formula": "Risk Score = 0.25 × Business Criticality + 0.20 × Historical Defect Risk + 0.20 × Change Risk + 0.15 × Production Usage + 0.10 × Network Risk + 0.10 × Unusual Behaviour Risk",
        "weights": WEIGHTS,
        "scale": "0-10",
        "note": "Historical Defect Risk is derived from actual Critical-severity records in the DefectHistory table.",
        "priority_thresholds": {
            "Critical": "≥ 8.0",
            "High": "≥ 6.0",
            "Medium": "≥ 4.0",
            "Low": "< 4.0",
        },
    }
