# config.py
import os
from pathlib import Path

basedir = Path(__file__).resolve().parent

class Config:
    # App
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    # Database - default to SQLite local file (vsxchange.db)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{basedir / 'vsxchange.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", os.environ.get("SECRET_KEY", "change-me-in-prod"))

    # Uploads
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(basedir / "uploads"))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

    # Cloudinary (optional) - use CLOUDINARY_URL or set CLOUDINARY_CLOUD_NAME, API_KEY, API_SECRET
    CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")

    # Other
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}