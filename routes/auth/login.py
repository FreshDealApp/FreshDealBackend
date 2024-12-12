from flask import Blueprint, request, jsonify
import logging

from services.communication import auth_code_generator
from services.communication import email_service
from werkzeug.security import check_password_hash
from models import db, User
from flask_jwt_extended import create_access_token

login_bp = Blueprint("login", __name__)

LOGIN_SUCCESS = False

# Configure logging to output to the console
logging.basicConfig(level=logging.INFO)


def get_client_ip():
    # Retrieve client IP address
    return request.headers.get("X-Forwarded-For", request.remote_addr) or "no_ip"

def get_user_by_email(email):
    return User.query.filter_by(email=email).first() if email else None

def get_user_by_phone(phone_number):
    return User.query.filter_by(phone_number=phone_number).first() if phone_number else None

def verify_password(user, password):
    if not user or not check_password_hash(user.password, password):
        return False
    return True


def generate_verification_code(ip=None,login_type=None):
    return auth_code_generator.generate_verification_code(ip=ip, identifier=login_type) # True, code


@login_bp.route("/login", methods=["POST"])
def login():
    global LOGIN_SUCCESS
    data = request.json
    email = data.get("email")
    phone_number = data.get("phone_number")
    password = data.get("password")
    verification_code = data.get("verification_code")
    step = data.get("step")  # "send_code", "verify_code", "skip_verification"
    login_type = data.get("login_type")  # "email", "phone_number"
    password_login = data.get("password_login")  # boolean
    ip = get_client_ip()

    logging.info(
        f"Login attempt from IP: {ip}, login_type: {login_type}, email: {email}, phone_number: {phone_number}, step: {step}, password_login: {password_login}"
    )

    if not login_type:  # check if login type is missing
        return jsonify({
            "success": False,
            "message": "Missing login type.",
            "details": {
                "error_code": "MISSING_LOGIN_TYPE"
            }
        }), 400



    if password_login:
        step = 'skip_verification'

    if not email and not phone_number:
        return jsonify({
            "success": False,
            "message": "Login using email or phone number",
            "details": {
                "error_code": "MISSING_EMAIL_OR_PHONE_NUMBER"
            }
        }), 400

    # Validate step
    if step not in ["send_code", "verify_code", "skip_verification"]:
        return jsonify({"success": False, "message": "Invalid step"}), 400

    user_data = None
    if login_type == "email":
        user_data = get_user_by_email(email=email)
    elif login_type == "phone_number":
        user_data = get_user_by_phone(phone_number=phone_number)

    if not user_data:
        return jsonify({"success": False, "message": "User not found"}), 404

    match step:
        case "skip_verification":
            LOGIN_SUCCESS = verify_password(user_data,password)

        case "send_code":
            response, message = generate_verification_code(ip=ip, login_type=login_type)
            if response:
                return jsonify({
                    "success": True,
                    "message": "Verification code sent successfully.",
                    "details": {}
                }), 200  # 200 OK
            else:
                return jsonify({
                    "success": False,
                    "message": message,  # Return the error message from generate_verification_code
                    "details": {}
                }), 400  # 400 Bad Request or other appropriate error code like 429 if rate limited

        case "verify_code":
            if not verification_code:
                return jsonify({
                    "success": False,
                    "message": f"Enter Verification Code sent to your {login_type}",
                    "details": {
                        "error_code": "MISSING_LOGIN_TYPE"
                    }
                }), 400
            response = auth_code_generator.verify_code(identifier=login_type,provided_code=verification_code)
            if response:
                LOGIN_SUCCESS = response
                #todo COMPLETE
        case _:
            return jsonify({"success": False, "message": "Invalid step"}), 400

    if LOGIN_SUCCESS:
        token = create_access_token(identity=user_data.id)
        return jsonify({"success": True, "token": token}), 200