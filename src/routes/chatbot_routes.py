from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from src.services.chatbot_service import ChatbotService
import traceback
import sys

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/api/chatbot/start', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Chatbot initial greeting and options",
    "description": "Returns the initial chatbot message and button options.",
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Initial chatbot message and buttons",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "message": {"type": "string", "example": "Hello! How can I assist you?"},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "example": [
                                    "Active order operations",
                                    "I want to cancel my order",
                                    "I want to change my address"
                                ]
                            }
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized - Missing or invalid token"
        }
    }
})
def chatbot_start():
    try:
        user_id = get_jwt_identity()
        response = ChatbotService.start_conversation(user_id)
        return jsonify(response), 200
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({"success": False, "message": str(e)}), 500


@chatbot_bp.route('/api/chatbot/order-status', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Get active order status",
    "description": "Returns the status of the user's active order.",
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Current order status returned",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "order_status": {"type": "string", "example": "In preparation"}
                        }
                    }
                }
            }
        },
        "404": {
            "description": "No active order found"
        }
    }
})
def chatbot_order_status():
    try:
        user_id = get_jwt_identity()
        response = ChatbotService.get_order_status(user_id)
        return jsonify(response), 200
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({"success": False, "message": str(e)}), 500


@chatbot_bp.route('/api/chatbot/cancel-order', methods=['POST'])
@jwt_required()
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Cancel the user's active order",
    "description": "Cancels the user's active order if it exists.",
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Order successfully cancelled",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "message": {"type": "string", "example": "Your order has been cancelled."}
                        }
                    }
                }
            }
        },
        "404": {
            "description": "No active order to cancel"
        }
    }
})
def chatbot_cancel_order():
    try:
        user_id = get_jwt_identity()
        response = ChatbotService.cancel_order(user_id)
        return jsonify(response), 200
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({"success": False, "message": str(e)}), 500


@chatbot_bp.route('/api/chatbot/update-address', methods=['POST'])
@jwt_required()
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Update user address",
    "description": "Adds a new address for the user and sets it as the primary address.",
    "security": [{"BearerAuth": []}],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "example": "Home"},
                        "longitude": {"type": "number", "example": 27.1428},
                        "latitude": {"type": "number", "example": 38.4237},
                        "street": {"type": "string", "example": "123 Elm St"},
                        "neighborhood": {"type": "string", "example": "Sunnydale"},
                        "district": {"type": "string", "example": "Downtown"},
                        "province": {"type": "string", "example": "Izmir"},
                        "country": {"type": "string", "example": "Turkey"},
                        "postalCode": {"type": "string", "example": "35000"},
                        "apartmentNo": {"type": "integer", "example": 5},
                        "doorNo": {"type": "string", "example": "A"}
                    }
                }
            }
        }
    },
    "responses": {
        "200": {
            "description": "Address successfully updated",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "message": {"type": "string", "example": "Your address has been successfully updated."}
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Invalid input"
        }
    }
})
def chatbot_update_address():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        new_address = {
            "title": data["title"],
            "longitude": data["longitude"],
            "latitude": data["latitude"],
            "street": data.get("street"),
            "neighborhood": data.get("neighborhood"),
            "district": data.get("district"),
            "province": data.get("province"),
            "country": data.get("country"),
            "postalCode": data.get("postalCode"),
            "apartmentNo": data.get("apartmentNo"),
            "doorNo": data.get("doorNo")
        }

        response = ChatbotService.update_user_address(user_id, new_address)
        return jsonify(response), 200
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({"success": False, "message": str(e)}), 500
