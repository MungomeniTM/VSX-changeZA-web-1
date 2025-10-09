# backend/app/routes/uploads.py
import os, uuid
from fastapi import APIRouter, File, UploadFile, Request, HTTPException
from app.core.config import UPLOAD_DIR
from pathlib import Path
from fastapi.responses import JSONResponse

router = APIRouter()

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {"png","jpg","jpeg","gif","webp","mp4","mov","webm"}

def _secure_filename(filename: str):
    if "." not in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    ext = filename.rsplit(".",1)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Invalid file type")
    return f"{uuid.uuid4().hex}.{ext}"

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    # optional auth check (you can expand)
    # save
    name = _secure_filename(file.filename)
    dest = os.path.join(UPLOAD_DIR, name)
    try:
        with open(dest, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save file")
    return {"url": f"/uploads/{name}"}