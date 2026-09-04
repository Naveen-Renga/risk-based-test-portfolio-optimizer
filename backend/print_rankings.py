from database import SessionLocal
from models import TestCase, DefectHistory
from routers.risk import calculate_risk_score

db = SessionLocal()
tcs = db.query(TestCase).all()
scored = []
for tc in tcs:
    risk = calculate_risk_score(tc, db=db)
    crit_count = risk['actual_critical_defect_count']
    scored.append({
        'id': tc.test_case_id,
        'name': tc.name,
        'time': tc.execution_time_minutes,
        'crit_defects': crit_count,
        'tc_crit_defects': tc.historical_critical_defect_count,
        'risk_score': risk['risk_score'],
    })

with open("rankings_clean.txt", "w") as f:
    f.write(f"{'RANK':<5} {'ID':<6} {'TIME':<6} {'CRIT_DEF':<10} {'TC_CRIT':<10} {'RISK_SCORE':<10}\n")
    f.write("="*55 + "\n")
    for i, s in enumerate(sorted(scored, key=lambda x: x['risk_score'], reverse=True), 1):
        f.write(f"{i:<5} {s['id']:<6} {s['time']:<6} {s['crit_defects']:<10} {s['tc_crit_defects']:<10} {s['risk_score']:<10}\n")

db.close()
