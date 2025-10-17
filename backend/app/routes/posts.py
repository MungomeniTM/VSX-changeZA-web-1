# backend/app/routes/posts.py
import os
import uuid
import json
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Post, Comment
from werkzeug.utils import secure_filename

UPLOAD_DIR = os.path.join(current_app.root_path, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

posts_bp = Blueprint('posts', __name__)

# -----------------------------
# Helpers
# -----------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png','jpg','jpeg','gif','webp','mp4','mov','webm'}

# -----------------------------
# Routes
# -----------------------------
@posts_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@posts_bp.route('/posts', methods=['GET'])
def list_posts():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 12))
    offset = (page - 1) * limit
    posts = Post.query.order_by(Post.created_at.desc()).offset(offset).limit(limit).all()
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
                "firstName": getattr(p.user, "first_name", None),
                "lastName": getattr(p.user, "last_name", None),
                "avatarUrl": None
            }
        })
    return jsonify({"posts": out, "hasMore": len(out) == limit})

@posts_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    text = request.form.get('text')
    media_file = request.files.get('media')
    media_url = None
    media_type = None

    if media_file and allowed_file(media_file.filename):
        filename = f"{uuid.uuid4().hex}_{secure_filename(media_file.filename)}"
        path = os.path.join(UPLOAD_DIR, filename)
        media_file.save(path)
        media_url = f"/uploads/{filename}"
        media_type = "video" if media_file.mimetype.startswith("video") else "image"

    post = Post(user_id=user.id, text=text, media=media_url, media_type=media_type)
    db.session.add(post)
    db.session.commit()
    db.session.refresh(post)

    return jsonify({
        "id": post.id,
        "text": post.text,
        "media": post.media,
        "mediaType": post.media_type,
        "approvals": post.approvals,
        "shares": post.shares,
        "createdAt": post.created_at.isoformat() if post.created_at else None,
        "user": {
            "id": user.id,
            "firstName": user.first_name,
            "lastName": user.last_name
        }
    })

@posts_bp.route('/posts/<int:post_id>/approve', methods=['POST'])
@jwt_required()
def approve_post(post_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    post.approvals = (post.approvals or 0) + 1
    db.session.commit()
    return jsonify({"approvals": post.approvals})

@posts_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at).all()
    out = []
    for c in comments:
        out.append({
            "id": c.id,
            "text": c.text,
            "createdAt": c.created_at.isoformat() if c.created_at else None,
            "user": {
                "id": c.user.id if c.user else None,
                "firstName": getattr(c.user, "first_name", None),
                "lastName": getattr(c.user, "last_name", None)
            }
        })
    return jsonify(out)

@posts_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}
    text_val = data.get("text")
    if not text_val:
        return jsonify({"error": "Missing 'text' field"}), 400

    comment = Comment(post_id=post_id, user_id=user.id, text=text_val)
    db.session.add(comment)
    db.session.commit()
    db.session.refresh(comment)

    return jsonify({
        "id": comment.id,
        "text": comment.text,
        "createdAt": comment.created_at.isoformat() if comment.created_at else None,
        "user": {
            "id": user.id,
            "firstName": user.first_name,
            "lastName": user.last_name
        }
    })