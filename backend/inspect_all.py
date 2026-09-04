from database import SessionLocal
from models import TestCase, DefectHistory
from routers.risk import calculate_risk_score

db = SessionLocal()
tcs = db.query(TestCase).order_by(TestCase.test_case_id).all()

print(f"{'ID':<6} {'Name':<35} {'Time':<5} {'CritDef':<8} {'TotDef':<8} {'Risk':<6} {'Efficiency':<10}")
print("="*85)
for tc in tcs:
    crit_count = db.query(DefectHistory).filter(DefectHistory.test_case_id == tc.test_case_id, DefectHistory.severity == 'Critical').count()
    tot_count = db.query(DefectHistory).filter(DefectHistory.test_case_id == tc.test_case_id).count()
    r = calculate_risk_score(tc, db=db)
    print(f"{tc.test_case_id:<6} {tc.name[:34]:<35} {tc.execution_time_minutes:<5} {crit_count:<8} {tot_count:<8} {r['risk_score']:<6} {r['efficiency_score']:<10}")

db.close()
