from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from seed_data import seed_database
from routers import auth, assessments, test_cases, risk, optimizer, events, experiments, security

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Risk-Based Test Portfolio Optimizer",
    description="Online Assessment Platform with Risk-Based Test Portfolio Optimization",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(assessments.router)
app.include_router(test_cases.router)
app.include_router(risk.router)
app.include_router(optimizer.router)
app.include_router(events.router)
app.include_router(experiments.router)
app.include_router(security.router)

@app.on_event("startup")
def startup():
    seed_database()

@app.get("/")
def root():
    return {"message": "Risk-Based Test Portfolio Optimizer API", "version": "1.0.0"}

@app.get("/api/dashboard/stats")
def dashboard_stats():
    from database import SessionLocal
    from models import TestCase, DefectHistory
    from routers.risk import calculate_risk_score

    db = SessionLocal()
    test_cases_list = db.query(TestCase).all()
    defects = db.query(DefectHistory).all()

    risk_scores = [calculate_risk_score(tc, db=db) for tc in test_cases_list]

    critical_count = sum(1 for r in risk_scores if r["priority_category"] == "Critical")
    high_count = sum(1 for r in risk_scores if r["priority_category"] == "High")
    avg_risk = round(sum(r["risk_score"] for r in risk_scores) / max(len(risk_scores), 1), 2)

    # Module-wise stats
    modules = {}
    for tc in test_cases_list:
        m = tc.module
        if m not in modules:
            modules[m] = {"test_count": 0, "total_defects": 0, "critical_defects": 0}
        modules[m]["test_count"] += 1
        modules[m]["total_defects"] += tc.historical_defect_count
        modules[m]["critical_defects"] += tc.historical_critical_defect_count

    # Journey-wise usage
    journeys = {}
    for tc in test_cases_list:
        j = tc.critical_user_journey
        if j not in journeys:
            journeys[j] = {"count": 0, "avg_usage": 0, "total_usage": 0}
        journeys[j]["count"] += 1
        journeys[j]["total_usage"] += tc.production_usage
    for j in journeys:
        journeys[j]["avg_usage"] = round(journeys[j]["total_usage"] / max(journeys[j]["count"], 1), 1)

    db.close()

    return {
        "total_test_cases": len(test_cases_list),
        "critical_tests": critical_count,
        "high_risk_tests": high_count,
        "average_risk_score": avg_risk,
        "total_defects": len(defects),
        "unresolved_defects": sum(1 for d in defects if not d.resolved),
        "modules": modules,
        "journeys": journeys,
        "risk_distribution": {
            "Critical": critical_count,
            "High": high_count,
            "Medium": sum(1 for r in risk_scores if r["priority_category"] == "Medium"),
            "Low": sum(1 for r in risk_scores if r["priority_category"] == "Low"),
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
