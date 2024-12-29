from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def phone_register():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    name = data.get('name')
    email = data.get('email')

    if not all([phone, password, name, email]):
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter((User.phone == phone) | (User.email == email)).first():
        return jsonify({'message': 'User with this phone or email already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(phone=phone, email=email, name=name, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'user': {'id': new_user.id, 'name': new_user.name, 'phone': new_user.phone, 'email': new_user.email}
    }), 201
