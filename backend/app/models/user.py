# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(120), nullable=True)
    last_name = Column(String(120), nullable=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(50), default="client")
    location = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)
    discoverable = Column(Boolean, default=True)