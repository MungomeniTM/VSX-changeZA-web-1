# backend/app/routes/me.py
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routes.posts import _get_user_from_auth  # reuse JWT helper
import json

router = APIRouter()

def parse_json_field(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except Exception:
        return []

@router.get("/me")
def get_profile(request: Request, db: Session = Depends(get_db)):
    user = _get_user_from_auth(db, request)
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Convert JSON fields back to lists
    return {
        "id": user.id,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "role": user.role,
        "location": user.location,
        "bio": user.bio,
        "rate": float(user.rate) if user.rate is not None else None,
        "availability": user.availability,
        "avatarUrl": user.avatarUrl,
        "discoverable": user.discoverable,
        "skills": parse_json_field(user.skills),
        "portfolio": parse_json_field(user.portfolio),
        "photos": parse_json_field(user.photos),
        "companies": parse_json_field(user.companies)
    }

@router.put("/me")
async def update_profile(request: Request, db: Session = Depends(get_db)):
    user = _get_user_from_auth(db, request)
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    data = await request.json()

    # Simple fields
    for key in ["firstName", "lastName", "role", "location", "bio", "rate", "availability", "avatarUrl", "discoverable"]:
        if key in data:
            val = data[key]
            if key == "discoverable":
                setattr(user, "discoverable", bool(val))
            elif key == "avatarUrl":
                setattr(user, "avatarUrl", val)
            elif key == "rate":
                try:
                    setattr(user, "rate", float(val))
                except:
                    pass
            else:
                setattr(user, key.lower(), val)

    # JSON fields
    for key in ["skills", "portfolio", "photos", "companies"]:
        if key in data:
            setattr(user, key.lower(), json.dumps(data[key]))

    db.commit()
    db.refresh(user)

    # return updated profile
    return {
        "id": user.id,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "role": user.role,
        "location": user.location,
        "bio": user.bio,
        "rate": float(user.rate) if user.rate is not None else None,
        "availability": user.availability,
        "avatarUrl": user.avatarUrl,
        "discoverable": user.discoverable,
        "skills": parse_json_field(user.skills),
        "portfolio": parse_json_field(user.portfolio),
        "photos": parse_json_field(user.photos),
        "companies": parse_json_field(user.companies)
    }