# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config  # Import your unified configuration

# Use SQLAlchemy connection string from Config class
DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

# For SQLite, allow multi-thread access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency that provides a database session and closes it automatically."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()