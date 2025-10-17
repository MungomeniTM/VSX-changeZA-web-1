from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.posts import _get_user_from_auth  # reuse JWT helper

router = APIRouter()

@router.get("/me")
def get_my_profile(request: Request, db: Session = Depends(get_db)):
    user = _get_user_from_auth(db, request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return _serialize_user(user)

@router.put("/me")
def update_my_profile(request: Request, payload: dict, db: Session = Depends(get_db)):
    user = _get_user_from_auth(db, request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Update fields safely
    user.first_name = payload.get("firstName", user.first_name)
    user.last_name = payload.get("lastName", user.last_name)
    user.role = payload.get("role", user.role)
    user.location = payload.get("location", user.location)
    user.bio = payload.get("bio", user.bio)
    user.rate = payload.get("rate", user.rate)
    user.availability = payload.get("availability", user.availability)
    user.skills = payload.get("skills", user.skills)
    user.portfolio = payload.get("portfolio", user.portfolio)
    user.photos = payload.get("photos", user.photos)
    user.companies = payload.get("companies", user.companies)
    user.avatarUrl = payload.get("avatarUrl", user.avatarUrl)
    user.discoverable = payload.get("discoverable", user.discoverable)

    db.add(user)
    db.commit()
    db.refresh(user)
    
    return _serialize_user(user)

# helper: serialize user to dict
def _serialize_user(user: User):
    return {
        "id": user.id,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "role": getattr(user, "role", None),
        "location": getattr(user, "location", None),
        "bio": getattr(user, "bio", None),
        "rate": getattr(user, "rate", None),
        "availability": getattr(user, "availability", None),
        "skills": getattr(user, "skills", []) or [],
        "portfolio": getattr(user, "portfolio", []) or [],
        "photos": getattr(user, "photos", []) or [],
        "companies": getattr(user, "companies", []) or [],
        "avatarUrl": getattr(user, "avatarUrl", None),
        "discoverable": getattr(user, "discoverable", True)
    }