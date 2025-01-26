from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.notification_service import NotificationService
from flasgger import swag_from

notification_bp = Blueprint('notification', __name__)
import logging

logger = logging.getLogger(__name__)

# Define documentation for update_push_token endpoint
update_push_token_doc = {
    "tags": ["Notifications"],
    "security": [{"BearerAuth": []}],
    "summary": "Update or register a device push token",
    "description": "Updates or registers a new push notification token for the current user's device",
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["push_token"],
                    "properties": {
                        "push_token": {
                            "type": "string",
                            "description": "The push notification token from the device",
                            "example": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
                        },
                        "device_type": {
                            "type": "string",
                            "description": "The type of device (ios/android)",
                            "enum": ["ios", "android", "unknown"],
                            "example": "ios"
                        },
                        "platform": {
                            "type": "string",
                            "description": "The platform of the device",
                            "example": "iOS 15.0"
                        }
                    }
                }
            }
        }
    },
    "responses": {
        "200": {
            "description": "Push token updated successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {
                                "type": "boolean",
                                "example": True
                            },
                            "message": {
                                "type": "string",
                                "example": "Push token updated successfully"
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {
                                "type": "boolean",
                                "example": False
                            },
                            "message": {
                                "type": "string",
                                "example": "Push token is required"
                            }
                        }
                    }
                }
            }
        }
    }
}

# Define documentation for delete_push_token endpoint
delete_push_token_doc = {
    "tags": ["Notifications"],
    "security": [{"BearerAuth": []}],
    "summary": "Deactivate a push token",
    "description": "Deactivates a push notification token for the current user's device",
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["push_token"],
                    "properties": {
                        "push_token": {
                            "type": "string",
                            "description": "The push notification token to deactivate",
                            "example": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
                        }
                    }
                }
            }
        }
    },
    "responses": {
        "200": {
            "description": "Token deactivated successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {
                                "type": "boolean",
                                "example": True
                            },
                            "message": {
                                "type": "string",
                                "example": "Token deactivated successfully"
                            }
                        }
                    }
                }
            }
        }
    }
}

# Define documentation for test_notification endpoint
test_notification_doc = {
    "tags": ["Notifications"],
    "security": [{"BearerAuth": []}],
    "summary": "Send test notification",
    "description": "Sends a test push notification to the current user's registered devices",
    "responses": {
        "200": {
            "description": "Test notification sent successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {
                                "type": "boolean",
                                "example": True
                            },
                            "message": {
                                "type": "string",
                                "example": "Test notification sent successfully"
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Failed to send notification",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {
                                "type": "boolean",
                                "example": False
                            },
                            "message": {
                                "type": "string",
                                "example": "Failed to send test notification"
                            }
                        }
                    }
                }
            }
        }
    }
}


@notification_bp.route('/users/push-token', methods=['POST'])
@jwt_required()
@swag_from(update_push_token_doc)
def update_push_token():
    """Update or register a device push token."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400

        if 'push_token' not in data:
            return jsonify({
                'success': False,
                'message': 'Push token is required'
            }), 400

        # Validate device_type if provided
        device_type = data.get('device_type', 'unknown')
        if device_type not in ['ios', 'android', 'unknown']:
            return jsonify({
                'success': False,
                'message': 'Invalid device type. Must be ios, android, or unknown'
            }), 400

        logger.info(f"Updating push token for user {user_id}")

        success, message = NotificationService.update_push_token(
            user_id=user_id,
            token=data['push_token'],
            device_type=device_type,
            platform=data.get('platform', 'unknown')
        )

        if not success:
            logger.error(f"Failed to update push token for user {user_id}: {message}")
            return jsonify({
                'success': False,
                'message': message
            }), 400

        logger.info(f"Successfully updated push token for user {user_id}")
        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        logger.error(f"Error in update_push_token: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@notification_bp.route('/users/push-token', methods=['DELETE'])
@jwt_required()
@swag_from(delete_push_token_doc)
def delete_push_token():
    """Deactivate a push token."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'push_token' not in data:
            return jsonify({
                'success': False,
                'message': 'Push token is required'
            }), 400

        logger.info(f"Deactivating push token for user {user_id}")

        success = NotificationService.deactivate_token(data['push_token'])
        if not success:
            logger.error(f"Failed to deactivate token for user {user_id}")
            return jsonify({
                'success': False,
                'message': 'Failed to deactivate token'
            }), 400

        logger.info(f"Successfully deactivated token for user {user_id}")
        return jsonify({
            'success': True,
            'message': 'Token deactivated successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error in delete_push_token: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@notification_bp.route('/notifications/test', methods=['POST'])
@jwt_required()
@swag_from(test_notification_doc)
def test_notification():
    """Send a test notification to the user's devices."""
    try:
        user_id = get_jwt_identity()

        logger.info(f"Sending test notification to user {user_id}")

        # Get user's devices first to check if they have any
        devices = NotificationService.get_user_devices(user_id)
        if not devices:
            return jsonify({
                'success': False,
                'message': 'No active devices found for this user'
            }), 400

        success = NotificationService.send_notification_to_user(
            user_id=user_id,
            title="Test Notification",
            body="This is a test notification from Fresh Deal!",
            data={
                "type": "test",
                "screen": "HomeScreen"
            }
        )

        if not success:
            logger.error(f"Failed to send test notification to user {user_id}")
            return jsonify({
                'success': False,
                'message': 'Failed to send test notification'
            }), 400

        logger.info(f"Successfully sent test notification to user {user_id}")
        return jsonify({
            'success': True,
            'message': 'Test notification sent successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error in test_notification: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


# New endpoint to get user's devices
@notification_bp.route('/users/devices', methods=['GET'])
@jwt_required()
def get_user_devices():
    """Get all devices registered for the current user."""
    try:
        user_id = get_jwt_identity()
        devices = NotificationService.get_user_devices(user_id)

        return jsonify({
            'success': True,
            'devices': devices
        }), 200

    except Exception as e:
        logger.error(f"Error in get_user_devices: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500