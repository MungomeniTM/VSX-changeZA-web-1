# backend/app/routes/search.py
from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User   # ORM model (adjust import if your user model path differs)
import json

router = APIRouter(tags=["search"])

def _normalize(v: Optional[str]):
    if not v:
        return None
    return v.strip().lower()

@router.get("/users")
def search_users(
    skill: Optional[str] = Query(None, description="Skill to search for"),
    location: Optional[str] = Query(None, description="City or province"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Return discoverable users matching skill/location.
    Matches are case-insensitive and partial.
    """
    skill_q = _normalize(skill)
    loc_q = _normalize(location)

    # load discoverable users (simple approach)
    q = db.query(User).filter(getattr(User, "discoverable", True) == True)

    # Basic fetch (we'll filter in python for skills array matching)
    offset = (page - 1) * limit
    users = q.offset(offset).limit(limit * 5).all()  # fetch a bit extra to allow filtering

    matched = []
    for u in users:
        # Read skills field — support JSON string or comma-separated string
        raw_skills = []
        if getattr(u, "skills", None):
            try:
                if isinstance(u.skills, (list, tuple)):
                    raw_skills = u.skills
                else:
                    raw_skills = json.loads(u.skills)
            except Exception:
                # fallback: comma separated
                raw_skills = [s.strip() for s in str(u.skills).split(",") if s.strip()]

        user_location = (getattr(u, "location", "") or "").lower()

        skill_match = False
        loc_match = False

        if skill_q:
            for s in raw_skills:
                if skill_q in str(s).lower():
                    skill_match = True
                    break

        if loc_q:
            if loc_q in user_location:
                loc_match = True

        # include user if:
        # - both queries present: at least one must match (OR semantics)
        # - only one present: must match that one
        include = False
        if skill_q and loc_q:
            include = skill_match or loc_match
        elif skill_q:
            include = skill_match
        elif loc_q:
            include = loc_match
        else:
            include = True  # no filters -> include

        if include:
            matched.append({
                "id": u.id,
                "firstName": getattr(u, "first_name", "") or "",
                "lastName": getattr(u, "last_name", "") or "",
                "role": getattr(u, "role", "") or "",
                "location": getattr(u, "location", "") or "",
                "skills": raw_skills,
                "avatarUrl": getattr(u, "avatar_url", None) or "",
                "photos": json.loads(u.photos) if getattr(u, "photos", None) else [],
                "companies": json.loads(u.companies) if getattr(u, "companies", None) else []
            })

        if len(matched) >= limit:
            break

    return {"results": matched, "page": page, "limit": limit, "count": len(matched)}