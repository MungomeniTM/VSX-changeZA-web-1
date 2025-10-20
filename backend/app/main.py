# main.py — unified, CORS-fixed, blueprint-ready
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

# Import models & db from your models module (you said you have a models folder)
# Make sure backend/app/models.py defines db, User, Post, Comment
from app.models import db, User, Post, Comment

# If you have a posts blueprint file, import it and register
try:
    from app.routes.posts import posts_bp
except Exception:
    posts_bp = None

# Config import (adjust path if needed)
from core.config import Config  # or from config import Config depending on your project

basedir = Path(__file__).resolve().parent

# allowed file extensions — keep in config normally
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'webm'}

def create_app(config_class=Config):
    app = Flask(__name__, static_folder="frontend", static_url_path="/")
    app.config.from_object(config_class)

    # ensure upload folder exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", str(basedir / "uploads")), exist_ok=True)

    # === CORS: explicitly allow your dev frontend origins and the important headers ===
    allowed_origins = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5500/",
        "http://localhost:5500/"
    ]
    CORS(app,
         resources={r"/*": {"origins": allowed_origins}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
         expose_headers=["Authorization"])

    # init db and jwt
    db.init_app(app)
    jwt = JWTManager(app)

    @app.route("/")
    def index():
        return jsonify({"message": "VSXchangeZA backend running."})

    # ------- AUTH ROUTES (keep simple and consistent) -------
    @app.route("/auth/register", methods=["POST"])
    def register():
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not username or not email or not password:
            return jsonify({"error": "username, email and password are required"}), 400

        if User.query.filter((User.username == username) | (User.email == email)).first():
            return jsonify({"error": "username or email already exists"}), 400

        pw_hash = generate_password_hash(password)
        user = User(username=username, email=email, password_hash=pw_hash)
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=7))
        return jsonify({"message": "user created", "access_token": access_token, "user": user.to_dict()}), 201

    @app.route("/auth/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        email_or_username = (data.get("email") or data.get("username") or "").strip()
        password = data.get("password", "")

        if not email_or_username or not password:
            return jsonify({"error": "Missing credentials"}), 400

        user = User.query.filter((User.email == email_or_username.lower()) | (User.username == email_or_username)).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_access_token(identity=user.id, expires_delta=timedelta(days=7))
        return jsonify({"access_token": token, "user": user.to_dict()}), 200

    # Provide both /auth/me and /me (frontend uses different names)
    @app.route("/auth/me", methods=["GET"])
    @jwt_required()
    def auth_me():
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        # return same shape for both endpoints
        return jsonify(user.to_dict())

    @app.route("/me", methods=["GET"])
    @jwt_required()
    def me():
        return auth_me()

    # ------- Upload endpoints (profile and post uploads) -------
    def allowed_file(filename):
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in ALLOWED_IMAGE_EXTENSIONS

    def save_file_locally(file_storage, subfolder=""):
        filename = secure_filename(file_storage.filename)
        if subfolder:
            dest_folder = Path(app.config.get("UPLOAD_FOLDER")) / subfolder
            dest_folder.mkdir(parents=True, exist_ok=True)
        else:
            dest_folder = Path(app.config.get("UPLOAD_FOLDER"))
        dest_path = dest_folder / f"{int(datetime.utcnow().timestamp())}_{filename}"
        file_storage.save(dest_path)
        # return a path accessible from frontend (relative)
        # Using host_url would cause issues behind proxy, so return relative path
        return f"/uploads/{subfolder}/{dest_path.name}" if subfolder else f"/uploads/{dest_path.name}"

    @app.route("/upload/profile", methods=["POST"])
    @jwt_required()
    def upload_profile_picture():
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400

        try:
            url = save_file_locally(file, subfolder="profiles")
        except Exception as e:
            app.logger.exception("Upload error")
            return jsonify({"error": "Upload failed", "details": str(e)}), 500

        user.profile_picture = url
        db.session.commit()
        return jsonify({"message": "Profile picture uploaded", "profile_picture": url})

    @app.route("/upload/post", methods=["POST"])
    @jwt_required()
    def upload_post_image():
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400

        try:
            url = save_file_locally(file, subfolder="posts")
        except Exception as e:
            app.logger.exception("Upload error")
            return jsonify({"error": "Upload failed", "details": str(e)}), 500

        post = Post(user_id=user.id, content=request.form.get("content", ""), image=url)
        db.session.add(post)
        db.session.commit()
        return jsonify({"message": "Post created with image", "post": post.to_dict()}), 201

    # Serve uploaded files locally (dev)
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        upload_dir = Path(app.config.get("UPLOAD_FOLDER"))
        # protect path traversal; we store one-level files inside folder or subfolders
        target = upload_dir / Path(filename)
        if not target.exists():
            return jsonify({"error": "Not found"}), 404
        # compute directory and filename for send_from_directory
        dirpath = str(target.parent)
        return send_from_directory(dirpath, target.name)

    # ------- Posts endpoints (list/create/approve/comment). Keep routes matching frontend paths -------
    @app.route("/posts", methods=["GET"])
    def list_posts():
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("limit", 12)), 50)
        offset = (page - 1) * per_page
        posts = Post.query.order_by(Post.created_at.desc()).offset(offset).limit(per_page).all()
        out = []
        for p in posts:
            out.append({
                "id": p.id,
                "text": getattr(p, "text", getattr(p, "content", "")),
                "media": getattr(p, "media", getattr(p, "image", None)),
                "mediaType": getattr(p, "media_type", None),
                "approvals": getattr(p, "approvals", 0),
                "shares": getattr(p, "shares", 0),
                "createdAt": p.created_at.isoformat() if p.created_at else None,
                "user": {
                    "id": p.author.id if p.author else None,
                    "firstName": getattr(p.author, "first_name", getattr(p.author, "display_name", None)),
                    "lastName": getattr(p.author, "last_name", None),
                    "avatarUrl": getattr(p.author, "profile_picture", None)
                }
            })
        return jsonify({"posts": out, "hasMore": len(out) == per_page})

    @app.route("/posts", methods=["POST"])
    @jwt_required()
    def create_post():
        # support both JSON body and multipart form data from frontend
        if request.content_type and request.content_type.startswith("multipart/"):
            text = request.form.get("text") or request.form.get("content") or ""
            media_file = request.files.get("media")
            media_url = None
            media_type = None
            if media_file and allowed_file(media_file.filename):
                filename = secure_filename(media_file.filename)
                stored = save_file_locally(media_file, subfolder="posts")
                media_url = stored
                media_type = "video" if media_file.mimetype.startswith("video") else "image"
        else:
            data = request.get_json() or {}
            text = data.get("text") or data.get("content") or ""
            media_url = data.get("media") or data.get("image")
            media_type = None

        if (not text) and (not media_url):
            return jsonify({"error": "content or media is required"}), 400

        current_user_id = get_jwt_identity()
        post = Post(user_id=current_user_id, text=text, media=media_url, media_type=media_type)
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
                "id": post.author.id if post.author else None,
                "firstName": getattr(post.author, "first_name", None),
                "lastName": getattr(post.author, "last_name", None),
            }
        }), 201

    @app.route("/posts/<int:post_id>/approve", methods=["POST"])
    @jwt_required()
    def approve_post(post_id):
        user_id = get_jwt_identity()
        post = Post.query.get(post_id)
        if not post:
            return jsonify({"error": "Post not found"}), 404
        post.approvals = (post.approvals or 0) + 1
        db.session.commit()
        return jsonify({"approvals": post.approvals})

    @app.route("/posts/<int:post_id>/comments", methods=["GET"])
    def get_comments(post_id):
        comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at).all()
        out = []
        for c in comments:
            out.append({
                "id": c.id,
                "text": getattr(c, "text", getattr(c, "content", "")),
                "createdAt": c.created_at.isoformat() if c.created_at else None,
                "user": {
                    "id": c.author.id if c.author else None,
                    "firstName": getattr(c.author, "first_name", None),
                    "lastName": getattr(c.author, "last_name", None)
                }
            })
        return jsonify(out)

    @app.route("/posts/<int:post_id>/comments", methods=["POST"])
    @jwt_required()
    def create_comment(post_id):
        data = request.get_json() or {}
        text_val = data.get("text") or data.get("content")
        if not text_val:
            return jsonify({"error": "Missing 'text' field"}), 400
        post = Post.query.get(post_id)
        if not post:
            return jsonify({"error": "post not found"}), 404
        current_user_id = get_jwt_identity()
        comment = Comment(post_id=post_id, user_id=current_user_id, content=text_val)
        db.session.add(comment)
        db.session.commit()
        db.session.refresh(comment)
        return jsonify({
            "id": comment.id,
            "text": comment.content if hasattr(comment, "content") else getattr(comment, "text", ""),
            "createdAt": comment.created_at.isoformat() if comment.created_at else None,
            "user": {
                "id": current_user_id,
                "firstName": getattr(comment.author, "first_name", None),
                "lastName": getattr(comment.author, "last_name", None)
            }
        }), 201

    # analytics (counts)
    @app.route("/analytics/summary", methods=["GET"])
    def analytics_summary():
        total_users = User.query.count()
        total_posts = Post.query.count()
        total_comments = Comment.query.count()
        recent_24h_posts = Post.query.filter(Post.created_at >= datetime.utcnow() - timedelta(days=1)).count()
        return jsonify({
            "users": total_users,
            "posts": total_posts,
            "comments": total_comments,
            "posts_last_24h": recent_24h_posts
        })

    # Register blueprint if present (keeps modular structure)
    if posts_bp:
        app.register_blueprint(posts_bp)  # posts blueprint defines same routes; registering for modularity

    # error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Server error")
        return jsonify({"error": "Server error"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)