# main.py
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.utils import secure_filename
from config import Config

# Optional Cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except Exception:
    CLOUDINARY_AVAILABLE = False

basedir = Path(__file__).resolve().parent

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="frontend", static_url_path="/")
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app, supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)

    @app.route("/")
    def index():
        return jsonify({"message": "VSXchangeZA backend running."})

    # --- MODELS ---
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(200), nullable=False)
        display_name = db.Column(db.String(120))
        bio = db.Column(db.Text)
        profile_picture = db.Column(db.String(300))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        posts = db.relationship("Post", backref="author", lazy=True)
        comments = db.relationship("Comment", backref="author", lazy=True)

        def to_dict(self):
            return {
                "id": self.id,
                "username": self.username,
                "email": self.email,
                "display_name": self.display_name,
                "bio": self.bio,
                "profile_picture": self.profile_picture,
                "created_at": self.created_at.isoformat(),
            }

    class Post(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        content = db.Column(db.Text, nullable=False)
        image = db.Column(db.String(300))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        comments = db.relationship("Comment", backref="post", lazy=True)

        def to_dict(self):
            return {
                "id": self.id,
                "user_id": self.user_id,
                "author": self.author.to_dict() if self.author else None,
                "content": self.content,
                "image": self.image,
                "created_at": self.created_at.isoformat(),
                "comments_count": len(self.comments),
            }

    class Comment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        content = db.Column(db.Text, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        def to_dict(self):
            return {
                "id": self.id,
                "post_id": self.post_id,
                "user_id": self.user_id,
                "author": self.author.to_dict() if self.author else None,
                "content": self.content,
                "created_at": self.created_at.isoformat(),
            }

    # --- HELPERS ---
    def allowed_file(filename):
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in app.config["ALLOWED_IMAGE_EXTENSIONS"]

    def save_file_locally(file_storage, subfolder=""):
        filename = secure_filename(file_storage.filename)
        if subfolder:
            dest_folder = Path(app.config["UPLOAD_FOLDER"]) / subfolder
            dest_folder.mkdir(parents=True, exist_ok=True)
        else:
            dest_folder = Path(app.config["UPLOAD_FOLDER"])
        dest_path = dest_folder / f"{int(datetime.utcnow().timestamp())}_{filename}"
        file_storage.save(dest_path)
        rel_path = dest_path.relative_to(app.config["UPLOAD_FOLDER"])
        return urljoin(request.host_url, f"uploads/{rel_path.as_posix()}")

    def upload_to_cloudinary(file_storage, folder="vsxchange"):
        if not CLOUDINARY_AVAILABLE or not app.config.get("CLOUDINARY_URL"):
            raise RuntimeError("Cloudinary not configured or not installed.")
        result = cloudinary.uploader.upload(
            file_storage,
            folder=folder,
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        return result.get("secure_url")

    # --- AUTH ROUTES ---
    @app.route("/auth/register", methods=["POST"])
    def register():
        try:
            data = request.get_json(force=True)
        except Exception:
            return jsonify({"error": "Invalid JSON payload"}), 400

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

        user = User.query.filter(
            (User.email == email_or_username.lower()) | (User.username == email_or_username)
        ).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_access_token(identity=user.id, expires_delta=timedelta(days=7))
        return jsonify({"access_token": token, "user": user.to_dict()}), 200

    @app.route("/auth/me", methods=["GET"])
    @jwt_required()
    def me():
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"user": user.to_dict()})

    # --- UPLOAD ROUTES ---
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
            if app.config.get("CLOUDINARY_URL") and CLOUDINARY_AVAILABLE:
                url = upload_to_cloudinary(file, folder=f"vsxchange/profiles/{user.id}")
            else:
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
            if app.config.get("CLOUDINARY_URL") and CLOUDINARY_AVAILABLE:
                url = upload_to_cloudinary(file, folder=f"vsxchange/posts/{user.id}")
            else:
                url = save_file_locally(file, subfolder="posts")
        except Exception as e:
            app.logger.exception("Upload error")
            return jsonify({"error": "Upload failed", "details": str(e)}), 500

        post = Post(user_id=user.id, content=request.form.get("content", ""), image=url)
        db.session.add(post)
        db.session.commit()
        return jsonify({"message": "Post created with image", "post": post.to_dict()}), 201

    # --- STATIC UPLOAD FILES ---
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        upload_dir = Path(app.config["UPLOAD_FOLDER"])
        safe_path = upload_dir / Path(filename).name
        if not safe_path.exists():
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(upload_dir, safe_path.name)

    # --- POSTS & COMMENTS ---
    @app.route("/posts", methods=["GET"])
    def list_posts():
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 50)
        posts = Post.query.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return jsonify({
            "items": [p.to_dict() for p in posts.items],
            "page": posts.page,
            "total": posts.total,
            "pages": posts.pages
        })

    @app.route("/posts/<int:post_id>", methods=["GET"])
    def get_post(post_id):
        p = Post.query.get_or_404(post_id)
        return jsonify({"post": p.to_dict()})

    @app.route("/posts/create", methods=["POST"])
    @jwt_required()
    def create_post():
        data = request.get_json() or {}
        content = data.get("content", "").strip()
        image = data.get("image")
        if not content and not image:
            return jsonify({"error": "content or image is required"}), 400
        current_user_id = get_jwt_identity()
        post = Post(user_id=current_user_id, content=content, image=image)
        db.session.add(post)
        db.session.commit()
        return jsonify({"message": "post created", "post": post.to_dict()}), 201

    @app.route("/posts/<int:post_id>/comments", methods=["POST"])
    @jwt_required()
    def create_comment(post_id):
        data = request.get_json() or {}
        content = data.get("content", "").strip()
        if not content:
            return jsonify({"error": "content required"}), 400
        post = Post.query.get(post_id)
        if not post:
            return jsonify({"error": "post not found"}), 404
        current_user_id = get_jwt_identity()
        comment = Comment(post_id=post_id, user_id=current_user_id, content=content)
        db.session.add(comment)
        db.session.commit()
        return jsonify({"message": "comment created", "comment": comment.to_dict()}), 201

    # --- ANALYTICS ---
    @app.route("/analytics/summary", methods=["GET"])
    def analytics_summary():
        total_users = User.query.count()
        total_posts = Post.query.count()
        total_comments = Comment.query.count()
        recent_24h_posts = Post.query.filter(
            Post.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        return jsonify({
            "users": total_users,
            "posts": total_posts,
            "comments": total_comments,
            "posts_last_24h": recent_24h_posts
        })

    # --- ERROR HANDLERS ---
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Server error")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    app.db = db
    app.User = User
    app.Post = Post
    app.Comment = Comment

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # ✅ Ensure DB file and upload folder exist safely
        Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)