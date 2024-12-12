from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models import db, User

register_bp = Blueprint("register", __name__)


@register_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    phone_number = data.get("phone_number")
    password = data.get("password")

    if not email and not phone_number:
        return jsonify({"success": False, "message": "Email or phone number is required"}), 400

    if not password:
        return jsonify({"success": False, "message": "Password is required"}), 400

    if email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"success": False, "message": "Email already exists"}), 409  # 409 conflict

    if phone_number:
        existing_phone_user = User.query.filter_by(phone_number=phone_number).first()
        if existing_phone_user:
            return jsonify({"success": False, "message": "Phone number already exists"}), 409

        # Additional checks for phone number format can be added here.

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, phone_number=phone_number, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True, "message": "User registered successfully"}), 201  # 201 created
