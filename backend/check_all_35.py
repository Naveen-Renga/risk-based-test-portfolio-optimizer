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
        'tc_hist_defects': tc.historical_defect_count,
        'tc_hist_crit_defects': tc.historical_critical_defect_count,
        'risk_score': risk['risk_score'],
    })

print("=== ALL 35 TEST CASES SORTED BY RISK SCORE DESC ===")
for i, s in enumerate(sorted(scored, key=lambda x: x['risk_score'], reverse=True), 1):
    print(f"{i:02d}. {s['id']}: Time={s['time']:<2}m | CritDefects(DefectHistory)={s['crit_defects']} | TC.hist_defects={s['tc_hist_defects']} | TC.hist_crit_defects={s['tc_hist_crit_defects']} | RiskScore={s['risk_score']}")

print("\n=== ALL 35 TEST CASES SORTED BY TEST_CASE_ID (FIFO ORDER) ===")
for i, s in enumerate(sorted(scored, key=lambda x: x['id']), 1):
    print(f"{i:02d}. {s['id']}: Time={s['time']:<2}m | CritDefects(DefectHistory)={s['crit_defects']} | TC.hist_defects={s['tc_hist_defects']} | TC.hist_crit_defects={s['tc_hist_crit_defects']} | RiskScore={s['risk_score']}")

db.close()
