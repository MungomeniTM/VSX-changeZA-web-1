# me.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User
import json

me_bp = Blueprint("me", __name__)

def parse_json_field(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except:
        return []

@me_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    # return full profile including JSON fields
    profile = user.to_dict()
    return jsonify(profile)

@me_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}

    # Update simple fields
    for key in ["firstName", "lastName", "role", "location", "bio", "rate", "availability", "avatarUrl", "discoverable"]:
        if key in data:
            if key == "discoverable":
                setattr(user, "discoverable", bool(data[key]))
            elif key == "avatarUrl":
                setattr(user, "avatarUrl", data[key])
            elif key == "rate":
                try:
                    setattr(user, "rate", float(data[key]))
                except:
                    pass
            else:
                setattr(user, key.lower(), data[key])

    # Update JSON fields
    for key in ["skills", "portfolio", "photos", "companies"]:
        if key in data:
            setattr(user, key.lower(), json.dumps(data[key]))

    db.session.commit()
    return jsonify(user.to_dict())