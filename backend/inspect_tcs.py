from database import SessionLocal
from models import TestCase, DefectHistory
from routers.risk import calculate_risk_score

db = SessionLocal()
tcs = db.query(TestCase).all()

print(f"{'ID':<6} {'Name':<35} {'Time':<5} {'CritDef(DB)':<12} {'TotalDef(TC)':<13} {'CritDef(TC)':<12} {'Risk':<6}")
print("="*95)
for tc in sorted(tcs, key=lambda x: x.test_case_id):
    r = calculate_risk_score(tc, db=db)
    crit_db = r['actual_critical_defect_count']
    print(f"{tc.test_case_id:<6} {tc.name[:34]:<35} {tc.execution_time_minutes:<5} {crit_db:<12} {tc.historical_defect_count:<13} {tc.historical_critical_defect_count:<12} {r['risk_score']:<6}")

db.close()
