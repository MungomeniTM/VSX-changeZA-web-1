from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.config import get_db, UPLOAD_DIR, engine
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
import os
import shutil

router = APIRouter(prefix="/users", tags=["Users"])

# ---------------------------
# Get user profile
# ---------------------------
@router.get("/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "skill": user.skill,
        "location": user.location,
        "portfolio_url": user.portfolio_url,
        "photo_url": f"/uploads/{user.photo}" if user.photo else None
    }

# ---------------------------
# Update user profile
# ---------------------------
@router.put("/{user_id}")
def update_user_profile(
    user_id: int,
    name: str = Form(...),
    skill: str = Form(...),
    location: str = Form(...),
    portfolio_url: str = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update basic fields
    user.name = name
    user.skill = skill
    user.location = location
    user.portfolio_url = portfolio_url

    # Handle photo upload
    if photo:
        photo_filename = f"user_{user_id}_{photo.filename}"
        file_path = os.path.join(UPLOAD_DIR, photo_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        user.photo = photo_filename

    db.commit()
    db.refresh(user)

    return {"message": "Profile updated successfully", "user": {
        "id": user.id,
        "name": user.name,
        "skill": user.skill,
        "location": user.location,
        "portfolio_url": user.portfolio_url,
        "photo_url": f"/uploads/{user.photo}" if user.photo else None
    }}