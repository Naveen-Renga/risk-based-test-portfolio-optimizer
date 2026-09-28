"""
conftest.py — Shared pytest fixtures for the backend test suite.

All tests use an in-memory SQLite database configured with StaticPool so all
connections share the exact same in-memory DB.
"""
import sys
import os
import pytest

# Make sure backend root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    from database import Base
    _engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=_engine)
    
    # Seed session-level data into the in-memory DB once
    Session = sessionmaker(bind=_engine)
    session = Session()
    _seed_test_data(session)
    session.close()

    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def db(engine):
    """Provide a fresh DB session per test."""
    _SessionLocal = sessionmaker(bind=engine)
    session = _SessionLocal()
    yield session
    session.close()


def _seed_test_data(session):
    """Insert minimal rows required for tests."""
    import hashlib
    from models import User, TestCase, DefectHistory, Assessment, Question

    def hpw(p):
        return hashlib.sha256(p.encode()).hexdigest()

    users = [
        User(id=1, username="student1",  full_name="Student One",  role="student",   password_hash=hpw("student123")),
        User(id=2, username="tester1",   full_name="Tester One",   role="tester",    password_hash=hpw("tester123")),
        User(id=3, username="testlead",  full_name="Test Lead One", role="test_lead", password_hash=hpw("lead123")),
        User(id=4, username="admin",     full_name="Admin User",    role="admin",     password_hash=hpw("admin123")),
    ]
    for u in users:
        session.merge(u)

    tcs = [
        TestCase(
            id=1, test_case_id="TC001", name="Login Security Test",
            module="Security", critical_user_journey="Access Control",
            description="Critical security test",
            business_criticality=9.0, historical_defect_count=5,
            historical_critical_defect_count=3,
            production_usage=9.0, change_risk=8.0, network_risk=7.0,
            unusual_behaviour_risk=7.0, execution_time_minutes=5.0,
            is_mandatory=True, current_status="Active"
        ),
        TestCase(
            id=2, test_case_id="TC002", name="Network Recovery Test",
            module="Network", critical_user_journey="Network Resilience",
            description="Network reconnection scenario",
            business_criticality=6.0, historical_defect_count=2,
            historical_critical_defect_count=1,
            production_usage=6.0, change_risk=5.0, network_risk=9.0,
            unusual_behaviour_risk=5.0, execution_time_minutes=4.0,
            is_mandatory=False, current_status="Active"
        ),
        TestCase(
            id=3, test_case_id="TC003", name="Submission Test",
            module="Submission", critical_user_journey="Exam Submission",
            description="Final submission pathway",
            business_criticality=8.0, historical_defect_count=4,
            historical_critical_defect_count=2,
            production_usage=8.0, change_risk=7.0, network_risk=4.0,
            unusual_behaviour_risk=5.0, execution_time_minutes=3.0,
            is_mandatory=False, current_status="Active"
        ),
        TestCase(
            id=4, test_case_id="TC004", name="Low Risk Feature Test",
            module="UI", critical_user_journey="Profile Update",
            description="Low risk UI test",
            business_criticality=2.0, historical_defect_count=1,
            historical_critical_defect_count=0,
            production_usage=2.0, change_risk=2.0, network_risk=2.0,
            unusual_behaviour_risk=2.0, execution_time_minutes=2.0,
            is_mandatory=False, current_status="Active"
        ),
    ]
    for tc in tcs:
        session.merge(tc)

    defects = [
        DefectHistory(id=1, test_case_id="TC001", defect_id="D001", severity="Critical",
                      module="Security", description="Auth bypass", detected_date="2024-01-01", resolved=False),
        DefectHistory(id=2, test_case_id="TC001", defect_id="D002", severity="Critical",
                      module="Security", description="XSS vulnerability", detected_date="2024-01-02", resolved=False),
        DefectHistory(id=3, test_case_id="TC003", defect_id="D003", severity="Critical",
                      module="Submission", description="Double submission", detected_date="2024-02-01", resolved=False),
    ]
    for d in defects:
        session.merge(d)

    a = Assessment(id=1, title="Test Assessment", description="Test",
                   duration_minutes=60, total_questions=2, passing_score=50, is_active=True)
    session.merge(a)

    q1 = Question(id=1, assessment_id=1, question_text="Q1?",
                  option_a="A", option_b="B", option_c="C", option_d="D",
                  correct_option="A", marks=1)
    q2 = Question(id=2, assessment_id=1, question_text="Q2?",
                  option_a="A", option_b="B", option_c="C", option_d="D",
                  correct_option="B", marks=1)
    session.merge(q1)
    session.merge(q2)
    session.commit()


@pytest.fixture(scope="session")
def test_app(engine):
    """Create a FastAPI test app wired to the in-memory DB."""
    from sqlalchemy.orm import sessionmaker
    from database import get_db
    from main import app

    _TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = _TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client(test_app):
    from fastapi.testclient import TestClient
    with TestClient(test_app) as c:
        yield c


@pytest.fixture(scope="session")
def tokens(client):
    """Log in all four roles and return their session tokens."""
    t = {}
    for creds in [
        ("student1",  "student123",  "student"),
        ("tester1",   "tester123",   "tester"),
        ("testlead",  "lead123",     "test_lead"),
        ("admin",     "admin123",    "admin"),
    ]:
        r = client.post("/api/auth/login", json={"username": creds[0], "password": creds[1]})
        assert r.status_code == 200, f"Login failed for {creds[0]}: {r.text}"
        t[creds[2]] = r.json()["token"]
    return t
