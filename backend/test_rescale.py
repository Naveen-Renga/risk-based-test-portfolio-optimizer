from database import SessionLocal
from models import TestCase, DefectHistory
from routers.risk import WEIGHTS, get_historical_critical_defect_count

db = SessionLocal()
tcs = db.query(TestCase).all()

# Find max critical defects across active test cases
max_crit_in_db = max(
    get_historical_critical_defect_count(tc.test_case_id, db) for tc in tcs
)
print(f"Max critical defects for any single test case in DefectHistory: {max_crit_in_db}")

def calc_risk_rescaled(tc, db):
    crit_count = get_historical_critical_defect_count(tc.test_case_id, db)
    # Scale defect_risk appropriately relative to max critical defects per test case (e.g. 2 or 3)
    max_crit_scale = max(max_crit_in_db, 2)
    defect_risk = min((crit_count / max_crit_scale) * 10.0, 10.0)

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
    return {
        'id': tc.test_case_id,
        'time': tc.execution_time_minutes,
        'crit_defects': crit_count,
        'risk_score': risk_score,
        'efficiency_score': round(risk_score / max(tc.execution_time_minutes, 0.1), 2)
    }

scored = [calc_risk_rescaled(tc, db) for tc in tcs]

# FIFO
fifo_sorted = sorted(scored, key=lambda x: x['id'])
fifo_sel = []
t = 0
for s in fifo_sorted:
    if t + s['time'] <= 60:
        t += s['time']
        fifo_sel.append(s)
fifo_time = sum(s['time'] for s in fifo_sel)
fifo_crit = sum(s['crit_defects'] for s in fifo_sel)
fifo_cdm = fifo_crit / fifo_time

# Risk-Score sorted
risk_sorted = sorted(scored, key=lambda x: x['risk_score'], reverse=True)
risk_sel = []
t = 0
for s in risk_sorted:
    if t + s['time'] <= 60:
        t += s['time']
        risk_sel.append(s)
risk_time = sum(s['time'] for s in risk_sel)
risk_crit = sum(s['crit_defects'] for s in risk_sel)
risk_cdm = risk_crit / risk_time

imp = ((risk_cdm - fifo_cdm) / fifo_cdm) * 100

print(f"FIFO @ 60m: Time={fifo_time:.1f}m, CritDefects={fifo_crit}, CD/min={fifo_cdm:.4f}")
print(f"RESCALED RISK @ 60m: Time={risk_time:.1f}m, CritDefects={risk_crit}, CD/min={risk_cdm:.4f}")
print(f"Dynamic Improvement: {imp:.1f}%")
print("Selected Risk IDs:", [s['id'] for s in risk_sel])

db.close()
