# backend/seed_user.py
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from passlib.context import CryptContext

# Setup password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check if any user exists
user = db.query(User).first()
if user:
    print(f"User already exists: {user.id} - {user.first_name} {user.last_name}")
else:
    # Create a test user with a hashed password
    hashed_password = pwd_context.hash("password123")
    test_user = User(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password_hash=hashed_password,
        role="Developer",
        location="Limpopo"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    print(f"✅ Created test user: {test_user.id} - {test_user.first_name} {test_user.last_name}")

db.close()