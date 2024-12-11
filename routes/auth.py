from flask import Flask, request, jsonify, Blueprint
import random


app = Flask(__name__)



# Helper functions to simulate sending SMS and email
def send_sms(phone_number, code):
    print(f"Sending SMS to {phone_number}: Your verification code is {code}")

def send_email(email, code):
    print(f"Sending Email to {email}: Your verification code is {code}")

# Route to handle login flow
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    step = data.get("step")  # "send_code", "verify_code", or "password_login"
    phone_number = data.get("phoneNumber")
    email = data.get("email")
    password = data.get("password")
    verification_code = data.get("verificationCode")

    # Prioritize phone number if both email and phone number are provided
    identifier = None
    if phone_number:
        identifier = phone_number
        user = USERS_DB.get(phone_number)
    elif email:
        identifier = email
        user = USERS_DB.get(email)
    else:
        return jsonify({"success": False, "message": "Phone number or email is required"}), 400

    if not user:
        return jsonify({"success": False, "message": "Account not registered"}), 404

    # Step 1: Send verification code
    if step == "send_code":
        if phone_number:
            code = str(random.randint(100000, 999999))
            USERS_DB[phone_number]["verificationCode"] = code
            send_sms(phone_number, code)
            return jsonify({"success": True, "message": "Verification code sent via SMS"})
        elif email:
            code = str(random.randint(100000, 999999))
            USERS_DB[email]["emailVerificationCode"] = code
            send_email(email, code)
            return jsonify({"success": True, "message": "Verification code sent via Email"})

    # Step 2: Verify code
    elif step == "verify_code":
        if phone_number:
            stored_code = user.get("verificationCode")
            if not stored_code or stored_code != verification_code:
                return jsonify({"success": False, "message": "Invalid or expired verification code"}), 401
            USERS_DB[phone_number]["verificationCode"] = None
            return jsonify({"success": True, "message": "Login successful", "userData": user})
