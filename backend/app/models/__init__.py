# backend/app/models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# initialize db
db = SQLAlchemy()

# --- User model ---
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    posts = db.relationship("Post", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "profile_picture": self.profile_picture,
        }

# --- Post model ---
class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text, nullable=True)
    media = db.Column(db.String(255), nullable=True)  # image/video URL
    media_type = db.Column(db.String(20), nullable=True)  # "image" or "video"
    approvals = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship("Comment", backref="post", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "media": self.media,
            "mediaType": self.media_type,
            "approvals": self.approvals,
            "shares": self.shares,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "user": {
                "id": self.author.id if self.author else None,
                "firstName": self.author.first_name if self.author else None,
                "lastName": self.author.last_name if self.author else None,
                "avatarUrl": self.author.profile_picture if self.author else None
            }
        }

# --- Comment model ---
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.content,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "user": {
                "id": self.author.id if self.author else None,
                "firstName": self.author.first_name if self.author else None,
                "lastName": self.author.last_name if self.author else None
            }
        }