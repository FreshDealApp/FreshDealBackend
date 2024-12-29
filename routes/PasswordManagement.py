from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')

    if not all([email, new_password]):
        return jsonify({'message': 'Missing required fields'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User does not exist'}), 404
    user.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'message': 'Password reset successfully'}), 200

@auth_bp.route('/update_password', methods=['POST'])
def update_password():
    data = request.get_json()
    user_id = data.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not all([user_id, old_password, new_password]):
        return jsonify({'message': 'Missing required fields'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User does not exist'}), 404

    if not check_password_hash(user.password, old_password):
        return jsonify({'message': 'Old password is incorrect'}), 400

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({'message': 'Password updated successfully'}), 200
