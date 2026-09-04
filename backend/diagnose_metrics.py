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
    })

# 1. FIFO
fifo_sorted = sorted(scored, key=lambda x: x['id'])
fifo_sel = []
t = 0
for s in fifo_sorted:
    if t + s['time'] <= 60:
        t += s['time']
        fifo_sel.append(s)
fifo_time = sum(s['time'] for s in fifo_sel)
fifo_crit = sum(s['crit_defects'] for s in fifo_sel)

# 2. Risk Score
risk_sorted = sorted(scored, key=lambda x: x['risk_score'], reverse=True)
risk_sel = []
t = 0
for s in risk_sorted:
    if t + s['time'] <= 60:
        t += s['time']
        risk_sel.append(s)
risk_time = sum(s['time'] for s in risk_sel)
risk_crit = sum(s['crit_defects'] for s in risk_sel)

# 3. Efficiency Score (Risk / Time)
eff_sorted = sorted(scored, key=lambda x: x['efficiency_score'], reverse=True)
eff_sel = []
t = 0
for s in eff_sorted:
    if t + s['time'] <= 60:
        t += s['time']
        eff_sel.append(s)
eff_time = sum(s['time'] for s in eff_sel)
eff_crit = sum(s['crit_defects'] for s in eff_sel)

f_cdm = fifo_crit / fifo_time
r_cdm = risk_crit / risk_time
e_cdm = eff_crit / eff_time

print(f"FIFO_CD_MIN: {f_cdm:.4f} (Defects={fifo_crit}, Time={fifo_time}m, Tests={len(fifo_sel)})")
print(f"RISK_SCORE_CD_MIN: {r_cdm:.4f} (Defects={risk_crit}, Time={risk_time}m, Tests={len(risk_sel)})")
print(f"EFF_SCORE_CD_MIN: {e_cdm:.4f} (Defects={eff_crit}, Time={eff_time}m, Tests={len(eff_sel)})")
print(f"RISK_SCORE_IMP: {((r_cdm - f_cdm)/f_cdm)*100:.2f}%")
print(f"EFF_SCORE_IMP: {((e_cdm - f_cdm)/f_cdm)*100:.2f}%")

db.close()
