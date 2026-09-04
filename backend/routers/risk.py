from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import TestCase

router = APIRouter(prefix="/api/risk", tags=["risk"])

WEIGHTS = {
    "business_criticality": 0.25,
    "historical_defect_risk": 0.20,
    "change_risk": 0.20,
    "production_usage": 0.15,
    "network_risk": 0.10,
    "unusual_behaviour_risk": 0.10,
}

def calculate_risk_score(tc):
    """Calculate risk score using the weighted formula."""
    # Normalize historical defect risk to 0-10 scale
    max_defects = 25  # Based on our seed data
    defect_risk = min((tc.historical_critical_defect_count / max(max_defects * 0.3, 1)) * 10, 10)

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
        "efficiency_score": round(risk_score / max(tc.execution_time_minutes, 0.1), 2)
    }

@router.get("/scores")
def get_risk_scores(db: Session = Depends(get_db)):
    test_cases = db.query(TestCase).all()
    results = []
    for tc in test_cases:
        risk = calculate_risk_score(tc)
        results.append({
            "test_case_id": tc.test_case_id,
            "name": tc.name,
            "module": tc.module,
            "critical_user_journey": tc.critical_user_journey,
            "execution_time_minutes": tc.execution_time_minutes,
            "is_mandatory": tc.is_mandatory,
            **risk
        })
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

@router.get("/weights")
def get_weights():
    return WEIGHTS

@router.get("/distribution")
def get_risk_distribution(db: Session = Depends(get_db)):
    test_cases = db.query(TestCase).all()
    distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for tc in test_cases:
        risk = calculate_risk_score(tc)
        distribution[risk["priority_category"]] += 1
    return distribution

@router.get("/formula")
def get_formula():
    return {
        "formula": "Risk Score = 0.25 × Business Criticality + 0.20 × Historical Defect Risk + 0.20 × Change Risk + 0.15 × Production Usage + 0.10 × Network Risk + 0.10 × Unusual Behaviour Risk",
        "weights": WEIGHTS,
        "scale": "0-10",
        "priority_thresholds": {
            "Critical": "≥ 8.0",
            "High": "≥ 6.0",
            "Medium": "≥ 4.0",
            "Low": "< 4.0"
        }
    }
