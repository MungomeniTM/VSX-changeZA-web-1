# backend/app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.models.user import User
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

class RegisterIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    password: str
    role: str | None = "client"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd.hash(payload.password)
    u = User(first_name=payload.first_name, last_name=payload.last_name, email=payload.email, password_hash=hashed, role=payload.role)
    db.add(u); db.commit(); db.refresh(u)
    return {"id": u.id, "email": u.email, "first_name": u.first_name, "role": u.role}

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == payload.email).first()
    if not u or not pwd.verify(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(u.id)})
    return {"token": token, "user": {"id": u.id, "first_name": u.first_name, "last_name": u.last_name, "email": u.email, "role": u.role, "location": u.location}}