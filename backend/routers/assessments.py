from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Assessment, Question, Submission
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from routers.auth import sessions
import json

router = APIRouter(prefix="/api/assessments", tags=["assessments"])

@router.get("/")
def get_assessments(db: Session = Depends(get_db)):
    assessments = db.query(Assessment).filter(Assessment.is_active == True).all()
    return [{
        "id": a.id, "title": a.title, "description": a.description,
        "duration_minutes": a.duration_minutes, "total_questions": a.total_questions,
        "passing_score": a.passing_score
    } for a in assessments]

@router.get("/{assessment_id}")
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {
        "id": a.id, "title": a.title, "description": a.description,
        "duration_minutes": a.duration_minutes, "total_questions": a.total_questions,
        "passing_score": a.passing_score
    }

@router.get("/{assessment_id}/questions")
def get_questions(assessment_id: int, db: Session = Depends(get_db)):
    questions = db.query(Question).filter(Question.assessment_id == assessment_id).all()
    return [{
        "id": q.id, "question_text": q.question_text,
        "option_a": q.option_a, "option_b": q.option_b,
        "option_c": q.option_c, "option_d": q.option_d,
        "marks": q.marks
    } for q in questions]

class StartRequest(BaseModel):
    user_id: int
    assessment_id: int
    token: str

@router.post("/start")
def start_assessment(req: StartRequest, db: Session = Depends(get_db)):
    # BUG 7 FIX: Verify token & ownership
    session_user = sessions.get(req.token)
    if not session_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if session_user["user_id"] != req.user_id and session_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: You cannot start an assessment for another student")

    existing = db.query(Submission).filter(
        Submission.user_id == req.user_id,
        Submission.assessment_id == req.assessment_id,
        Submission.status == "in_progress"
    ).first()
    if existing:
        return {"submission_id": existing.id, "status": "resumed", "started_at": str(existing.started_at)}

    submission = Submission(
        user_id=req.user_id,
        assessment_id=req.assessment_id,
        answers=json.dumps({}),
        status="in_progress"
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return {"submission_id": submission.id, "status": "started", "started_at": str(submission.started_at)}

class SaveAnswerRequest(BaseModel):
    submission_id: int
    question_id: int
    answer: str
    token: str

@router.post("/save-answer")
def save_answer(req: SaveAnswerRequest, db: Session = Depends(get_db)):
    # BUG 7 FIX: Ownership authorization check
    session_user = sessions.get(req.token)
    if not session_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    submission = db.query(Submission).filter(Submission.id == req.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.user_id != session_user["user_id"] and session_user["role"] != "admin":
        raise HTTPException(status_code=403, detail=f"Forbidden: You do not own submission {req.submission_id}")

    if submission.status == "submitted":
        raise HTTPException(status_code=400, detail="Assessment already submitted")

    answers = json.loads(submission.answers) if submission.answers else {}
    answers[str(req.question_id)] = req.answer
    submission.answers = json.dumps(answers)
    db.commit()
    return {"status": "saved", "answers_count": len(answers)}

class SubmitRequest(BaseModel):
    submission_id: int
    token: str

@router.post("/submit")
def submit_assessment(req: SubmitRequest, db: Session = Depends(get_db)):
    # BUG 7 FIX: Ownership verification
    session_user = sessions.get(req.token)
    if not session_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    submission = db.query(Submission).filter(Submission.id == req.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.user_id != session_user["user_id"] and session_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: You cannot submit another user's assessment")

    if submission.status == "submitted":
        raise HTTPException(status_code=400, detail="Already submitted")

    answers = json.loads(submission.answers) if submission.answers else {}
    questions = db.query(Question).filter(Question.assessment_id == submission.assessment_id).all()

    total_marks = 0
    score = 0
    for q in questions:
        total_marks += q.marks
        if answers.get(str(q.id)) == q.correct_option:
            score += q.marks

    submission.score = score
    submission.total_marks = total_marks
    submission.status = "submitted"
    submission.submitted_at = datetime.utcnow()
    db.commit()

    return {
        "status": "submitted",
        "score": score,
        "total_marks": total_marks,
        "percentage": round((score / total_marks * 100) if total_marks > 0 else 0, 1),
        "submitted_at": str(submission.submitted_at)
    }

@router.get("/submission/{submission_id}")
def get_submission(submission_id: int, token: str, db: Session = Depends(get_db)):
    session_user = sessions.get(token)
    if not session_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.user_id != session_user["user_id"] and session_user["role"] not in ["admin", "test_lead"]:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot view another student's submission result")

    questions = db.query(Question).filter(Question.assessment_id == submission.assessment_id).all()
    answers = json.loads(submission.answers) if submission.answers else {}

    question_results = []
    for q in questions:
        user_answer = answers.get(str(q.id), None)
        question_results.append({
            "id": q.id, "question_text": q.question_text,
            "option_a": q.option_a, "option_b": q.option_b,
            "option_c": q.option_c, "option_d": q.option_d,
            "correct_option": q.correct_option if submission.status == "submitted" else None,
            "user_answer": user_answer,
            "is_correct": user_answer == q.correct_option if submission.status == "submitted" else None,
            "marks": q.marks
        })

    return {
        "id": submission.id,
        "status": submission.status,
        "score": submission.score,
        "total_marks": submission.total_marks,
        "percentage": round((submission.score / submission.total_marks * 100) if submission.total_marks and submission.total_marks > 0 else 0, 1),
        "started_at": str(submission.started_at),
        "submitted_at": str(submission.submitted_at) if submission.submitted_at else None,
        "questions": question_results
    }

@router.get("/user/{user_id}/submissions")
def get_user_submissions(user_id: int, token: str, db: Session = Depends(get_db)):
    session_user = sessions.get(token)
    if not session_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if session_user["user_id"] != user_id and session_user["role"] not in ["admin", "test_lead"]:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot view another user's submission history")

    submissions = db.query(Submission).filter(Submission.user_id == user_id).all()
    result = []
    for s in submissions:
        assessment = db.query(Assessment).filter(Assessment.id == s.assessment_id).first()
        result.append({
            "id": s.id,
            "assessment_title": assessment.title if assessment else "Unknown",
            "status": s.status,
            "score": s.score,
            "total_marks": s.total_marks,
            "percentage": round((s.score / s.total_marks * 100) if s.total_marks and s.total_marks > 0 else 0, 1),
            "started_at": str(s.started_at),
            "submitted_at": str(s.submitted_at) if s.submitted_at else None
        })
    return result
