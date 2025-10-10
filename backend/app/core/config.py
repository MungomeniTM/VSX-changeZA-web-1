# backend/app/core/config.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database URL — adjust if needed
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vsxchangeza.db")

# Engine setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Base class for models
Base = declarative_base()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# API settings
API_PREFIX = "/api"
UPLOAD_DIR = "uploads"