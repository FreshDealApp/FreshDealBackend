from flasgger import swag_from
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.restaurant_punishment_service import RestaurantPunishmentService
from src.models import User
from datetime import datetime, UTC

restaurant_punishment_bp = Blueprint('restaurant_punishment', __name__)

@restaurant_punishment_bp.route('/restaurants/<int:restaurant_id>/punish', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Restaurant Punishment'],
    'summary': 'Issue a punishment to a restaurant',
    'description': 'Support team members can issue temporary or permanent punishments to restaurants',
    'parameters': [
        {
            'name': 'restaurant_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the restaurant to punish'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'duration_type': {
                        'type': 'string',
                        'enum': ['THREE_DAYS', 'ONE_WEEK', 'ONE_MONTH', 'THREE_MONTHS', 'PERMANENT'],
                        'description': 'Duration of the punishment'
                    },
                    'reason': {
                        'type': 'string',
                        'description': 'Reason for the punishment'
                    }
                },
                'required': ['duration_type', 'reason']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Punishment issued successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'punishment_id': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Invalid request data'
        },
        403: {
            'description': 'Not authorized as support team member'
        },
        404: {
            'description': 'Restaurant not found'
        }
    },
    'security': [{'Bearer': []}]
})
def punish_restaurant(restaurant_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.role != 'support':
        return jsonify({
            "success": False,
            "message": "Only support team members can issue punishments",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        }), 403

    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "message": "No data provided",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        }), 400

    response, status_code = RestaurantPunishmentService.issue_punishment(
        restaurant_id,
        data,
        current_user_id
    )
    response["timestamp"] = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(response), status_code

@restaurant_punishment_bp.route('/orders/<int:order_id>/refund', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Restaurant Punishment'],
    'summary': 'Issue a refund for an order',
    'description': 'Support team members can issue refunds for orders',
    'parameters': [
        {
            'name': 'order_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the order to refund'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'amount': {
                        'type': 'number',
                        'format': 'float',
                        'description': 'Amount to refund'
                    },
                    'reason': {
                        'type': 'string',
                        'description': 'Reason for the refund'
                    }
                },
                'required': ['amount', 'reason']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Refund issued successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'refund_id': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Invalid request data'
        },
        403: {
            'description': 'Not authorized as support team member'
        },
        404: {
            'description': 'Order not found'
        }
    },
    'security': [{'Bearer': []}]
})
def issue_refund(order_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.role != 'support':
        return jsonify({
            "success": False,
            "message": "Only support team members can issue refunds",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        }), 403

    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "message": "No data provided",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        }), 400

    if not data.get('amount') or not data.get('reason'):
        return jsonify({
            "success": False,
            "message": "Amount and reason are required",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        }), 400

    response, status_code = RestaurantPunishmentService.issue_refund(
        order_id,
        data,
        current_user_id
    )
    response["timestamp"] = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(response), status_code

@restaurant_punishment_bp.route('/restaurants/<int:restaurant_id>/status', methods=['GET'])
@swag_from({
    'tags': ['Restaurant Punishment'],
    'summary': 'Get restaurant punishment status',
    'description': 'Get the current punishment status of a restaurant',
    'parameters': [
        {
            'name': 'restaurant_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the restaurant to check'
        }
    ],
    'responses': {
        200: {
            'description': 'Restaurant status retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'is_punished': {'type': 'boolean'},
                    'punishment_type': {'type': 'string'},
                    'end_date': {'type': 'string', 'format': 'date-time'},
                    'reason': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Restaurant not found'
        }
    }
})
def get_restaurant_status(restaurant_id):
    status = RestaurantPunishmentService.check_restaurant_status(restaurant_id)
    status["timestamp"] = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(status), 200