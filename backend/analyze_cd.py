import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import TestCase, DefectHistory
from routers.risk import calculate_risk_score

db = SessionLocal()
tcs = db.query(TestCase).filter(TestCase.current_status == 'Active').all()

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
        'efficiency_score': risk['efficiency_score'],
        'risk_density': round(risk['risk_score'] / tc.execution_time_minutes, 4),
        'cd_density': round(crit_count / tc.execution_time_minutes, 4)
    })

print("=== ALL 35 TEST CASES ===")
for s in sorted(scored, key=lambda x: x['id']):
    print(f"ID={s['id']:<6} Time={s['time']:<2}m  CritDefects={s['crit_defects']}  RiskScore={s['risk_score']:<4}  EffScore={s['efficiency_score']:<4}  CD/min_density={s['cd_density']}")

# 1. BASELINE (FIFO)
fifo_sorted = sorted(scored, key=lambda x: x['id'])
fifo_sel = []
fifo_t = 0
fifo_cd = 0
for s in fifo_sorted:
    if fifo_t + s['time'] <= 60:
        fifo_t += s['time']
        fifo_cd += s['crit_defects']
        fifo_sel.append(s)

print("\n--- 1. BASELINE (FIFO) @ 60m ---")
print(f"Count: {len(fifo_sel)}, Exec Time: {fifo_t:.1f}m, Crit Defects Detected: {fifo_cd}")
print(f"Baseline CD/min: {fifo_cd / max(fifo_t, 0.1):.4f}")
print("Selected IDs:", [s['id'] for s in fifo_sel])

# 2. CURRENT EXPERIMENTS OPTIMIZER (Sorted strictly by risk_score DESC)
risk_sorted = sorted(scored, key=lambda x: x['risk_score'], reverse=True)
risk_sel = []
risk_t = 0
risk_cd = 0
for s in risk_sorted:
    if risk_t + s['time'] <= 60:
        risk_t += s['time']
        risk_cd += s['crit_defects']
        risk_sel.append(s)

print("\n--- 2. CURRENT EXPERIMENTS OPTIMIZER (Sorted by risk_score DESC) @ 60m ---")
print(f"Count: {len(risk_sel)}, Exec Time: {risk_t:.1f}m, Crit Defects Detected: {risk_cd}")
print(f"Risk-Score CD/min: {risk_cd / max(risk_t, 0.1):.4f}")
print("Selected IDs:", [s['id'] for s in risk_sel])

fifo_cd_min = fifo_cd / max(fifo_t, 0.1)
risk_cd_min = risk_cd / max(risk_t, 0.1)
imp_risk = ((risk_cd_min - fifo_cd_min) / fifo_cd_min) * 100
print(f"Improvement over FIFO: {imp_risk:.1f}%")

# 3. OPTIMIZER BY EFFICIENCY SCORE / RISK DENSITY (risk_score / execution_time)
eff_sorted = sorted(scored, key=lambda x: x['efficiency_score'], reverse=True)
eff_sel = []
eff_t = 0
eff_cd = 0
for s in eff_sorted:
    if eff_t + s['time'] <= 60:
        eff_t += s['time']
        eff_cd += s['crit_defects']
        eff_sel.append(s)

print("\n--- 3. OPTIMIZER BY EFFICIENCY SCORE (risk_score / time) @ 60m ---")
print(f"Count: {len(eff_sel)}, Exec Time: {eff_t:.1f}m, Crit Defects Detected: {eff_cd}")
print(f"Efficiency-Score CD/min: {eff_cd / max(eff_t, 0.1):.4f}")
print("Selected IDs:", [s['id'] for s in eff_sel])

eff_cd_min = eff_cd / max(eff_t, 0.1)
imp_eff = ((eff_cd_min - fifo_cd_min) / fifo_cd_min) * 100
print(f"Improvement over FIFO: {imp_eff:.1f}%")

# 4. OPTIMIZER BY DYNAMIC KNAPSACK / DENSITY SOLVER WITH HARD CONSTRAINTS
# What if we sort by risk_score / execution_time (efficiency_score) or use fractional knapsack?
# Let's inspect test case execution times and risk scores in detail
db.close()
