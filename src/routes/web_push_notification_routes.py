import json
import sys
import traceback
import logging
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from src.services.web_push_notification_service import WebPushNotificationService

web_push_bp = Blueprint('web_push', __name__, url_prefix='/web-push')
logger = logging.getLogger(__name__)

# Swagger documentation
web_push_subscribe_doc = {
    'tags': ['Web Push Notifications'],
    'description': 'Subscribe a browser for web push notifications',
    'parameters': [
        {
            'name': 'subscription',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'endpoint': {
                        'type': 'string',
                        'description': 'The push service endpoint'
                    },
                    'keys': {
                        'type': 'object',
                        'properties': {
                            'p256dh': {
                                'type': 'string',
                                'description': 'User public key'
                            },
                            'auth': {
                                'type': 'string',
                                'description': 'Auth secret'
                            }
                        }
                    }
                }
            },
            'required': True,
            'description': 'The PushSubscription object from the browser'
        }
    ],
    'responses': {
        '200': {
            'description': 'Web push subscription registered successfully'
        },
        '400': {
            'description': 'Bad request'
        },
        '500': {
            'description': 'Internal server error'
        }
    }
}

web_push_test_doc = {
    'tags': ['Web Push Notifications'],
    'description': 'Send a test web push notification to the user\'s browsers',
    'responses': {
        '200': {
            'description': 'Test web notification sent successfully'
        },
        '400': {
            'description': 'Bad request'
        },
        '500': {
            'description': 'Internal server error'
        }
    }
}

vapid_public_key_doc = {
    'tags': ['Web Push Notifications'],
    'description': 'Get the VAPID public key for web push notifications',
    'responses': {
        '200': {
            'description': 'Public key retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean'
                    },
                    'publicKey': {
                        'type': 'string'
                    }
                }
            }
        },
        '500': {
            'description': 'Internal server error'
        }
    }
}


@web_push_bp.route('/subscribe', methods=['POST'])
@jwt_required()
@swag_from(web_push_subscribe_doc)
def web_push_subscribe():
    """Subscribe a browser for web push notifications."""
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "body": request.get_json() if request.is_json else {}
        }
        print(json.dumps({"request": request_log}, indent=2))

        data = request.get_json()
        if not data:
            error_response = {
                'success': False,
                'message': 'No data provided'
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        subscription = data.get('subscription')
        if not subscription:
            error_response = {
                'success': False,
                'message': 'Missing required field: subscription'
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        # Get user agent if available
        user_agent = request.headers.get('User-Agent')

        user_id = get_jwt_identity()
        success, message = WebPushNotificationService.register_web_push_token(
            user_id,
            subscription,
            user_agent
        )

        if not success:
            error_response = {
                'success': False,
                'message': message
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        response = {
            'success': True,
            'message': message
        }
        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in web_push_subscribe: {str(e)}")
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            'success': False,
            'message': 'Internal server error'
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@web_push_bp.route('/vapid-public-key', methods=['GET'])
@swag_from(vapid_public_key_doc)
def get_vapid_public_key():
    """Get the VAPID public key for web push notifications."""
    try:
        public_key = os.environ.get('VAPID_PUBLIC_KEY')

        if not public_key:
            error_response = {
                'success': False,
                'message': 'VAPID public key not configured'
            }
            print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
            return jsonify(error_response), 500

        response = {
            'success': True,
            'publicKey': public_key
        }
        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in get_vapid_public_key: {str(e)}")
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            'success': False,
            'message': 'Internal server error'
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@web_push_bp.route('/test', methods=['POST'])
@jwt_required()
@swag_from(web_push_test_doc)
def test_web_notification():
    """Send a test web push notification to the user's browsers."""
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "body": request.get_json() if request.is_json else {}
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        logger.info(f"Sending test web notification to user {user_id}")

        success = WebPushNotificationService.send_notification_to_user_web(
            user_id=user_id,
            title="Test Web Notification",
            body="This is a test web notification from Fresh Deal!",
            data={
                "type": "test"
            },
            icon="/static/images/logo.png"
        )

        if not success:
            logger.error(f"Failed to send test web notification to user {user_id}")
            error_response = {
                'success': False,
                'message': 'Failed to send test web notification'
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        logger.info(f"Successfully sent test web notification to user {user_id}")
        response = {
            'success': True,
            'message': 'Test web notification sent successfully'
        }
        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in test_web_notification: {str(e)}")
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            'success': False,
            'message': 'Internal server error'
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500