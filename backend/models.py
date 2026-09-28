from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    role = Column(String)  # student, tester, test_lead, admin
    created_at = Column(DateTime, default=datetime.utcnow)

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    duration_minutes = Column(Integer)
    total_questions = Column(Integer)
    passing_score = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    question_text = Column(Text)
    option_a = Column(String)
    option_b = Column(String)
    option_c = Column(String)
    option_d = Column(String)
    correct_option = Column(String)
    marks = Column(Integer, default=1)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    answers = Column(Text)  # JSON string
    score = Column(Integer, nullable=True)
    total_marks = Column(Integer, nullable=True)
    status = Column(String, default="in_progress")  # in_progress, submitted
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)

class TestCase(Base):
    __tablename__ = "test_cases"
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(String, unique=True, index=True)  # TC001
    name = Column(String)
    module = Column(String)
    critical_user_journey = Column(String)
    description = Column(Text)
    business_criticality = Column(Float)
    historical_defect_count = Column(Integer)
    historical_critical_defect_count = Column(Integer)
    production_usage = Column(Float)
    change_risk = Column(Float)
    network_risk = Column(Float)
    unusual_behaviour_risk = Column(Float)
    execution_time_minutes = Column(Float)
    is_mandatory = Column(Boolean, default=False)
    current_status = Column(String, default="Active")  # Active, Deprecated, Under Review

class DefectHistory(Base):
    __tablename__ = "defect_history"
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(String, ForeignKey("test_cases.test_case_id"))
    defect_id = Column(String)
    severity = Column(String)  # Critical, High, Medium, Low
    module = Column(String)
    description = Column(Text)
    detected_date = Column(String)
    resolved = Column(Boolean, default=False)
    resolution_time_hours = Column(Float, nullable=True)

class OverrideLog(Base):
    __tablename__ = "override_logs"
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(String)
    old_priority = Column(Integer)
    new_priority = Column(Integer)
    reason = Column(Text)
    performed_by = Column(String)
    role = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class EventLog(Base):
    __tablename__ = "event_logs"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String)
    event_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sequence_number = Column(Integer)
    payload = Column(Text)
    status = Column(String)  # processed, duplicate, rejected, delayed

class SecurityLog(Base):
    __tablename__ = "security_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    user = Column(String)
    role = Column(String)
    result = Column(String)  # ALLOWED, DENIED
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
