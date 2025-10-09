# backend/app/routes/posts.py
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.post import Post
from app.models.user import User
from app.models.comment import Comment
from app.core.config import UPLOAD_DIR

router = APIRouter()

# ensure upload dir exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _get_user_from_auth(db: Session, request: Request):
    # Dev-friendly: if Authorization header contains an integer token, treat it as user id.
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        # if token is a plain integer (dev), return that user
        try:
            uid = int(token)
            u = db.query(User).get(uid)
            if u:
                return u
        except Exception:
            pass
        # else you might decode JWT here in prod
    # fallback: return first user (dev convenience)
    return db.query(User).first()

@router.get("/posts")
def list_posts(db: Session = Depends(get_db), page: int = 1, limit: int = 12):
    offset = (page - 1) * limit
    posts = db.query(Post).order_by(Post.created_at.desc()).offset(offset).limit(limit).all()
    out = []
    for p in posts:
        out.append({
            "id": p.id,
            "text": p.text,
            "media": p.media,
            "mediaType": p.media_type,
            "approvals": p.approvals,
            "shares": p.shares,
            "createdAt": p.created_at.isoformat() if p.created_at else None,
            "user": {
                "id": p.user.id if p.user else None,
                "first_name": getattr(p.user, "first_name", None),
                "last_name": getattr(p.user, "last_name", None),
                "avatarUrl": None
            }
        })
    return {"posts": out, "hasMore": len(out) == limit}

@router.post("/posts")
def create_post(
    request: Request,
    text: str = Form(None),
    media: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = _get_user_from_auth(db, request)
    if not user:
        raise HTTPException(status_code=401, detail="No user available (ensure you have at least one user in DB or provide a token)")

    media_url = None
    media_type = None
    if media:
        ext = os.path.splitext(media.filename)[1] or ""
        fname = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(UPLOAD_DIR, fname)
        with open(dest, "wb") as f:
            shutil.copyfileobj(media.file, f)
        media_url = f"/uploads/{fname}"
        media_type = "video" if media.content_type and media.content_type.startswith("video") else "image"

    post = Post(user_id=user.id, text=text, media=media_url, media_type=media_type)
    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "id": post.id,
        "text": post.text,
        "media": post.media,
        "mediaType": post.media_type,
        "approvals": post.approvals,
        "shares": post.shares,
        "createdAt": post.created_at.isoformat() if post.created_at else None,
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }

@router.post("/posts/{post_id}/approve")
def approve_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    user = _get_user_from_auth(db, request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.approvals = (post.approvals or 0) + 1
    db.commit()
    return {"approvals": post.approvals}

@router.get("/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at).all()
    out = []
    for c in comments:
        out.append({
            "id": c.id,
            "text": c.text,
            "createdAt": c.created_at.isoformat() if c.created_at else None,
            "user": {
                "id": c.user.id if c.user else None,
                "first_name": getattr(c.user, "first_name", None),
                "last_name": getattr(c.user, "last_name", None),
            }
        })
    return out

@router.post("/posts/{post_id}/comments")
def create_comment(post_id: int, request: Request, payload: dict = None, db: Session = Depends(get_db)):
    # Accept both JSON body and form data 'text' for convenience
    user = _get_user_from_auth(db, request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    body = {}
    try:
        body = request.json()  # may fail for form
    except Exception:
        pass
    text = None
    if body and isinstance(body, dict):
        text = body.get("text")
    if not text:
        # try to read form body
        form = request._body if hasattr(request, "_body") else None
    # fallback: read request body raw (fastapi normally passes json)
    req_text = None
    try:
        req = request._json if hasattr(request, "_json") else None
    except Exception:
        req = None

    # Best option: read from Starlette Request body quickly (synchronous; ok small)
    try:
        import json as _json
        raw = request.stream()
    except Exception:
        pass

    # Simpler approach: accept JSON via fetch -> earlier frontend sends JSON
    try:
        j = request.json()
    except Exception:
        j = None

    # Instead rely on FastAPI auto mapping: if client sends JSON, FastAPI would pass data in function param (not used here)
    # For reliability, expect frontend sends JSON. We'll manually attempt to parse request._body if available.
    data = None
    try:
        body_bytes = request._body if hasattr(request, "_body") else None
    except Exception:
        body_bytes = None

    # Ultimately: support standard JSON POSTs that the frontend sends using fetch(JSON).
    # So we will attempt to read body via request.json() (works with normal FastAPI routing when param declared).
    try:
        data = request.json()
    except Exception:
        data = None

    # Best compromise: read text from request._body_bytes (if any) or expect payload param
    text_val = None
    try:
        # If FastAPI passed json parsed into payload param (rare), use it.
        if isinstance(payload, dict):
            text_val = payload.get("text")
    except Exception:
        pass

    # If still None, attempt to parse request body synchronously from request._body (Starlette internal)
    try:
        body_raw = request._body if hasattr(request, "_body") else None
        if body_raw:
            import json as _json
            parsed = _json.loads(body_raw.decode() if isinstance(body_raw, (bytes, bytearray)) else body_raw)
            text_val = text_val or parsed.get("text")
    except Exception:
        pass

    if not text_val:
        # Last fallback: raise
        raise HTTPException(status_code=400, detail="Missing 'text' in body")

    comment = Comment(post_id=post_id, user_id=user.id, text=text_val)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "text": comment.text,
        "createdAt": comment.created_at.isoformat() if comment.created_at else None,
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }