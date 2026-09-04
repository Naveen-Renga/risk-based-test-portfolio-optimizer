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
        'risk_score': risk['risk_score'],
        'cd_density': round(crit_count / max(tc.execution_time_minutes, 0.1), 3),
        'risk_density': round(risk['risk_score'] / max(tc.execution_time_minutes, 0.1), 3),
    })

print("=== TOP 15 BY RISK SCORE ===")
for s in sorted(scored, key=lambda x: x['risk_score'], reverse=True)[:15]:
    print(f"{s['id']}: Time={s['time']}m CritDef={s['crit_defects']} Risk={s['risk_score']} CD_Density={s['cd_density']} Risk_Density={s['risk_density']}")

print("\n=== TOP 15 BY RISK DENSITY (Risk / Time) ===")
for s in sorted(scored, key=lambda x: x['risk_density'], reverse=True)[:15]:
    print(f"{s['id']}: Time={s['time']}m CritDef={s['crit_defects']} Risk={s['risk_score']} CD_Density={s['cd_density']} Risk_Density={s['risk_density']}")

db.close()
