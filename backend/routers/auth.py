import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["auth"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Simple in-memory session store (for demo purposes)
sessions = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: int
    username: str
    full_name: str
    role: str

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    import uuid
    token = str(uuid.uuid4())
    sessions[token] = {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }
    return LoginResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
    )

@router.post("/logout")
def logout(token: str):
    sessions.pop(token, None)
    return {"message": "Logged out"}

@router.get("/me")
def get_current_user(token: str):
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[token]

def require_role(token: str, allowed_roles: list):
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = sessions[token]
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Access denied. Required role: {', '.join(allowed_roles)}")
    return user

@router.get("/users")
def get_users(token: str, db: Session = Depends(get_db)):
    # Require valid session
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Require admin role
    user = sessions[token]
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied: Admin role required")
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role} for u in users]
