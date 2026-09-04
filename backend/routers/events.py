from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import EventLog
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/events", tags=["events"])

# In-memory state machine for simulation
class AssessmentStateMachine:
    VALID_TRANSITIONS = {
        "IDLE": ["START_EXAM"],
        "STARTED": ["ANSWER_SUBMITTED", "ANSWER_SAVED", "TIMER_UPDATED", "NETWORK_DISCONNECTED", "SUBMIT_EXAM"],
        "ANSWERING": ["ANSWER_SUBMITTED", "ANSWER_SAVED", "TIMER_UPDATED", "NETWORK_DISCONNECTED", "SUBMIT_EXAM"],
        "DISCONNECTED": ["NETWORK_RECONNECTED"],
        "SUBMITTED": [],  # Terminal state
    }

    def __init__(self):
        self.state = "IDLE"
        self.answers = {}
        self.events_processed = []
        self.events_rejected = []
        self.duplicate_count = 0
        self.processed_event_ids = set()

    def process_event(self, event_type: str, event_id: str, payload: dict = None):
        result = {"event_type": event_type, "event_id": event_id, "previous_state": self.state}

        # Idempotency check
        if event_id in self.processed_event_ids:
            self.duplicate_count += 1
            result["status"] = "DUPLICATE_REJECTED"
            result["reason"] = f"Event {event_id} already processed (idempotency check)"
            result["new_state"] = self.state
            self.events_rejected.append(result)
            return result

        # State validation
        valid_events = self.VALID_TRANSITIONS.get(self.state, [])

        # Special handling for state transitions
        if event_type == "START_EXAM" and self.state == "IDLE":
            self.state = "STARTED"
            result["status"] = "PROCESSED"
            result["reason"] = "Exam started successfully"
        elif event_type == "ANSWER_SUBMITTED" and self.state in ["STARTED", "ANSWERING"]:
            self.state = "ANSWERING"
            if payload and "question_id" in payload:
                self.answers[payload["question_id"]] = payload.get("answer", "")
            result["status"] = "PROCESSED"
            result["reason"] = "Answer recorded"
        elif event_type == "ANSWER_SAVED" and self.state in ["STARTED", "ANSWERING"]:
            result["status"] = "PROCESSED"
            result["reason"] = "Answer autosaved"
        elif event_type == "TIMER_UPDATED" and self.state in ["STARTED", "ANSWERING"]:
            result["status"] = "PROCESSED"
            result["reason"] = "Timer updated"
        elif event_type == "NETWORK_DISCONNECTED" and self.state in ["STARTED", "ANSWERING"]:
            self.state = "DISCONNECTED"
            result["status"] = "PROCESSED"
            result["reason"] = "Network disconnection detected, state preserved"
        elif event_type == "NETWORK_RECONNECTED" and self.state == "DISCONNECTED":
            self.state = "ANSWERING" if self.answers else "STARTED"
            result["status"] = "PROCESSED"
            result["reason"] = "Network reconnected, state restored"
        elif event_type == "SUBMIT_EXAM" and self.state in ["STARTED", "ANSWERING"]:
            self.state = "SUBMITTED"
            result["status"] = "PROCESSED"
            result["reason"] = f"Exam submitted with {len(self.answers)} answers"
        elif event_type == "ANSWER_SAVED" and self.state == "SUBMITTED":
            result["status"] = "REJECTED"
            result["reason"] = "Late save event rejected - exam already submitted"
            self.events_rejected.append(result)
            result["new_state"] = self.state
            return result
        else:
            result["status"] = "REJECTED"
            result["reason"] = f"Invalid transition: {event_type} not allowed in state {self.state}. Valid events: {valid_events}"
            self.events_rejected.append(result)
            result["new_state"] = self.state
            return result

        self.processed_event_ids.add(event_id)
        result["new_state"] = self.state
        self.events_processed.append(result)
        return result


class EventInput(BaseModel):
    event_type: str
    event_id: Optional[str] = None
    sequence_number: int = 0
    payload: Optional[dict] = None

class SimulationRequest(BaseModel):
    events: List[EventInput]
    scenario_name: str = "Custom Simulation"

@router.post("/simulate")
def simulate_events(req: SimulationRequest, db: Session = Depends(get_db)):
    machine = AssessmentStateMachine()
    results = []

    for event in req.events:
        eid = event.event_id or str(uuid.uuid4())[:8]
        result = machine.process_event(event.event_type, eid, event.payload)
        results.append(result)

        # Log to database
        log = EventLog(
            event_id=eid,
            event_type=event.event_type,
            sequence_number=event.sequence_number,
            payload=str(event.payload) if event.payload else "",
            status=result["status"]
        )
        db.add(log)

    db.commit()

    state_corrupted = machine.state not in ["IDLE", "STARTED", "ANSWERING", "SUBMITTED", "DISCONNECTED"]

    return {
        "scenario_name": req.scenario_name,
        "total_events": len(req.events),
        "processed_count": len(machine.events_processed),
        "rejected_count": len(machine.events_rejected),
        "duplicate_count": machine.duplicate_count,
        "final_state": machine.state,
        "answers_recorded": len(machine.answers),
        "state_corrupted": state_corrupted,
        "results": results,
    }

@router.post("/simulate/duplicate")
def simulate_duplicate(db: Session = Depends(get_db)):
    """Pre-built scenario: Duplicate answer event"""
    req = SimulationRequest(
        scenario_name="Duplicate Answer Event",
        events=[
            EventInput(event_type="START_EXAM", event_id="EVT001", sequence_number=1),
            EventInput(event_type="ANSWER_SUBMITTED", event_id="EVT002", sequence_number=2, payload={"question_id": "Q1", "answer": "A"}),
            EventInput(event_type="ANSWER_SUBMITTED", event_id="EVT002", sequence_number=3, payload={"question_id": "Q1", "answer": "A"}),
            EventInput(event_type="SUBMIT_EXAM", event_id="EVT003", sequence_number=4),
        ]
    )
    return simulate_events(req, db)

@router.post("/simulate/delayed")
def simulate_delayed(db: Session = Depends(get_db)):
    """Pre-built scenario: Delayed save after submission"""
    req = SimulationRequest(
        scenario_name="Delayed Save After Submission",
        events=[
            EventInput(event_type="START_EXAM", event_id="EVT010", sequence_number=1),
            EventInput(event_type="ANSWER_SUBMITTED", event_id="EVT011", sequence_number=2, payload={"question_id": "Q1", "answer": "B"}),
            EventInput(event_type="SUBMIT_EXAM", event_id="EVT012", sequence_number=3),
            EventInput(event_type="ANSWER_SAVED", event_id="EVT013", sequence_number=4, payload={"question_id": "Q1", "answer": "C"}),
        ]
    )
    return simulate_events(req, db)

@router.post("/simulate/out-of-order")
def simulate_out_of_order(db: Session = Depends(get_db)):
    """Pre-built scenario: Out-of-order events"""
    req = SimulationRequest(
        scenario_name="Out-of-Order Assessment Events",
        events=[
            EventInput(event_type="ANSWER_SAVED", event_id="EVT020", sequence_number=3, payload={"question_id": "Q1", "answer": "A"}),
            EventInput(event_type="ANSWER_SUBMITTED", event_id="EVT021", sequence_number=2, payload={"question_id": "Q1", "answer": "A"}),
            EventInput(event_type="START_EXAM", event_id="EVT022", sequence_number=1),
        ]
    )
    return simulate_events(req, db)

@router.get("/logs")
def get_event_logs(db: Session = Depends(get_db)):
    logs = db.query(EventLog).order_by(EventLog.timestamp.desc()).limit(100).all()
    return [{
        "id": l.id, "event_id": l.event_id, "event_type": l.event_type,
        "timestamp": str(l.timestamp), "sequence_number": l.sequence_number,
        "status": l.status
    } for l in logs]
