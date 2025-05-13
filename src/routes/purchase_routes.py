from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
import json
import traceback
import sys

from src.services.purchase_service import (
    create_purchase_order_service,
    handle_restaurant_response_service,
    get_restaurant_purchases_service,
    get_user_active_orders_service,
    get_user_previous_orders_service,
    get_order_details_service,
)
from src.services.gamification_services import add_discount_point

purchase_bp = Blueprint("purchase", __name__)


@purchase_bp.route("/purchase", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Create a new purchase order from cart items",
    "description": (
            "Creates one or more purchase orders for all items in the user's cart. "
            "If the cart is empty or any item exceeds available stock, the request will fail. "
            "The resulting purchase orders will have a **PENDING** status until the restaurant accepts or rejects them. "
            "If `is_delivery = false`, you can optionally include `pickup_notes`. "
            "If `is_delivery = true`, you **must** provide `address_id` or delivery address details.\n\n"
            "Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): 2025-04-19 15:42:48\n"
            "Current User's Login: emreutkan"
    ),
    "security": [{"BearerAuth": []}],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["is_delivery"],
                    "properties": {
                        "is_delivery": {
                            "type": "boolean",
                            "description": "Flag to indicate if this is a delivery order",
                            "example": False
                        },
                        "address_id": {
                            "type": "integer",
                            "description": "ID of the saved address to use for delivery",
                            "example": 1
                        },
                        "pickup_notes": {
                            "type": "string",
                            "description": "Optional notes for pickup orders (ignored if is_delivery=true)",
                            "example": "Will pick up at 6pm"
                        },
                        "delivery_address": {
                            "type": "string",
                            "description": "Required only if is_delivery=true and address_id not provided",
                            "example": "123 Main St"
                        },
                        "delivery_district": {
                            "type": "string",
                            "description": "District/area name for analytics",
                            "example": "Downtown"
                        },
                        "delivery_province": {
                            "type": "string",
                            "description": "Province/state name",
                            "example": "Istanbul"
                        },
                        "delivery_country": {
                            "type": "string",
                            "description": "Country name",
                            "example": "Turkey"
                        },
                        "delivery_notes": {
                            "type": "string",
                            "description": "Optional notes for delivery orders",
                            "example": "Please leave at the back door"
                        }
                    }
                },
                "examples": {
                    "pickup_order": {
                        "summary": "Example (Pickup)",
                        "value": {
                            "is_delivery": False,
                            "pickup_notes": "Will pick up at 6pm"
                        }
                    },
                    "delivery_order_with_saved_address": {
                        "summary": "Example (Delivery with saved address)",
                        "value": {
                            "is_delivery": True,
                            "address_id": 1,
                            "delivery_notes": "Please leave at the back door"
                        }
                    },
                    "delivery_order_with_new_address": {
                        "summary": "Example (Delivery with new address)",
                        "value": {
                            "is_delivery": True,
                            "delivery_address": "123 Main St",
                            "delivery_district": "Downtown",
                            "delivery_province": "Istanbul",
                            "delivery_country": "Turkey",
                            "delivery_notes": "Please leave at the back door"
                        }
                    }
                }
            }
        }
    },
    "responses": {
        "201": {
            "description": "Purchase orders created successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "example": "Purchase order created successfully, waiting for restaurant approval"
                            },
                            "purchases": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer", "example": 101},
                                        "listing_id": {"type": "integer", "example": 12},
                                        "quantity": {"type": "integer", "example": 2},
                                        "total_price": {"type": "string", "example": "25.99"},
                                        "status": {
                                            "type": "string",
                                            "enum": ["PENDING", "ACCEPTED", "REJECTED", "COMPLETED"],
                                            "example": "PENDING"
                                        },
                                        "is_delivery": {"type": "boolean", "example": True},
                                        "address_title": {"type": "string", "example": "Home"},
                                        "delivery_address": {"type": "string", "example": "123 Main St"},
                                        "delivery_district": {"type": "string", "example": "Downtown"},
                                        "delivery_province": {"type": "string", "example": "Istanbul"},
                                        "delivery_country": {"type": "string", "example": "Turkey"},
                                        "delivery_notes": {"type": "string", "example": "Please leave at the back door"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Bad Request (e.g., Cart is empty or insufficient stock)",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "example": "Cart is empty or insufficient stock for some listing."
                            }
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized - Missing or invalid authorization token",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "msg": {"type": "string", "example": "Missing Authorization Header"}
                        }
                    }
                }
            }
        },
        "500": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "example": "An error occurred"},
                            "error": {"type": "string", "example": "Traceback or error details"}
                        }
                    }
                }
            }
        }
    }
})
def create_purchase_order():
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "data": request.get_json()
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        data = request.get_json() or {}
        response, status = create_purchase_order_service(user_id, data)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while creating the purchase order.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@purchase_bp.route("/purchase/<int:purchase_id>/response", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Restaurant response to a purchase order",
    "description": (
            "Allows the restaurant (owner) to accept or reject a **PENDING** purchase order. "
            "If the order is **rejected**, stock is restored. "
            "If the current user is not the owner of the restaurant associated with this purchase, the request is forbidden."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "purchase_id",
            "in": "path",
            "schema": {"type": "integer"},
            "required": True,
            "description": "ID of the purchase order to respond to",
            "example": 101
        }
    ],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["accept", "reject"],
                            "description": "Action to take on the purchase order"
                        }
                    },
                    "example": {
                        "action": "accept"
                    }
                }
            }
        }
    },
    "responses": {
        "200": {
            "description": "Successfully processed restaurant response",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "example": "Purchase accepted successfully"},
                            "purchase": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "example": 101},
                                    "status": {
                                        "type": "string",
                                        "enum": ["PENDING", "ACCEPTED", "REJECTED", "COMPLETED"],
                                        "example": "ACCEPTED"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Invalid action or purchase is not in a valid state",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden - The current user is not the restaurant owner for this purchase"
        },
        "404": {
            "description": "Purchase not found"
        },
        "500": {
            "description": "Internal server error"
        }
    }
})
def restaurant_response(purchase_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "data": request.get_json()
        }
        print(json.dumps({"request": request_log}, indent=2))

        restaurant_id = get_jwt_identity()
        action = request.json.get('action')
        response, status = handle_restaurant_response_service(
            purchase_id,
            restaurant_id,
            action
        )

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while processing the restaurant response.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@purchase_bp.route("/restaurant/<int:restaurant_id>/purchases", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Get all purchases for a restaurant",
    "description": (
            "Retrieves all purchase orders linked to a specific restaurant. "
            "Typically, only the restaurant owner should be allowed to view these orders."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "restaurant_id",
            "in": "path",
            "schema": {"type": "integer"},
            "required": True,
            "description": "ID of the restaurant",
            "example": 5
        }
    ],
    "responses": {
        "200": {
            "description": "List of purchases retrieved successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "purchases": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer", "example": 101},
                                        "user_id": {"type": "integer", "example": 7},
                                        "listing_id": {"type": "integer", "example": 12},
                                        "listing_title": {"type": "string", "example": "Box of cupcakes"},
                                        "quantity": {"type": "integer", "example": 2},
                                        "total_price": {"type": "string", "example": "25.99"},
                                        "purchase_date": {
                                            "type": "string",
                                            "format": "date-time",
                                            "example": "2025-01-19T12:34:56"
                                        },
                                        "status": {
                                            "type": "string",
                                            "enum": ["PENDING", "ACCEPTED", "REJECTED", "COMPLETED"],
                                            "example": "PENDING"
                                        },
                                        "is_delivery": {"type": "boolean", "example": False},
                                        "delivery_address": {"type": "string", "example": None},
                                        "delivery_notes": {"type": "string", "example": None},
                                        "completion_image_url": {
                                            "type": "string",
                                            "example": "https://example.com/uploads/order-101.png"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "401": {"description": "Unauthorized - Invalid or missing token"},
        "403": {"description": "Forbidden - User is not authorized to view these purchases"},
        "500": {"description": "Internal server error"}
    }
})
def get_restaurant_purchases(restaurant_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        response, status = get_restaurant_purchases_service(restaurant_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching restaurant purchases.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@purchase_bp.route("/purchases/<int:purchase_id>/accept", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Accept a purchase order",
    "description": (
            "Allows the restaurant owner to explicitly accept a **PENDING** purchase order. "
            "Once accepted, the purchase can later be marked as completed with a completion image."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "purchase_id",
            "in": "path",
            "schema": {"type": "integer"},
            "required": True,
            "description": "ID of the purchase order to accept",
            "example": 101
        }
    ],
    "responses": {
        "200": {
            "description": "Purchase successfully accepted",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "example": "Purchase accepted successfully"},
                            "purchase": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "example": 101},
                                    "status": {
                                        "type": "string",
                                        "enum": ["ACCEPTED"],
                                        "example": "ACCEPTED"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Purchase cannot be accepted (e.g., already rejected or completed)"
        },
        "401": {
            "description": "Unauthorized - Invalid or missing token"
        },
        "403": {
            "description": "Forbidden - Current user is not the restaurant owner"
        },
        "404": {
            "description": "Purchase not found"
        },
        "500": {
            "description": "Internal server error"
        }
    }
})
def accept_purchase(purchase_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        restaurant_id = get_jwt_identity()
        response, status = handle_restaurant_response_service(purchase_id, restaurant_id, 'accept')
        add_discount_point(purchase_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while accepting the purchase.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@purchase_bp.route("/purchases/<int:purchase_id>/reject", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Reject a purchase order",
    "description": (
            "Allows the restaurant owner to explicitly reject a **PENDING** purchase order. "
            "Once rejected, the stock is restored for the associated listing."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "purchase_id",
            "in": "path",
            "schema": {"type": "integer"},
            "required": True,
            "description": "ID of the purchase order to reject",
            "example": 101
        }
    ],
    "responses": {
        "200": {
            "description": "Purchase successfully rejected",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "example": "Purchase rejected successfully"},
                            "purchase": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "example": 101},
                                    "status": {
                                        "type": "string",
                                        "enum": ["REJECTED"],
                                        "example": "REJECTED"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Purchase cannot be rejected (already accepted or completed)"
        },
        "401": {
            "description": "Unauthorized - Invalid or missing token"
        },
        "403": {
            "description": "Forbidden - Current user is not the restaurant owner"
        },
        "404": {
            "description": "Purchase not found"
        },
        "500": {
            "description": "Internal server error"
        }
    }
})
def reject_purchase(purchase_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        restaurant_id = get_jwt_identity()
        response, status = handle_restaurant_response_service(purchase_id, restaurant_id, 'reject')

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while rejecting the purchase.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@purchase_bp.route("/user/orders/active", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Get user's active orders",
    "description": (
            "Retrieves all active (PENDING or ACCEPTED) orders for the current user. "
            "Active orders are those that have not been completed or rejected yet."
    ),
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Active orders retrieved successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "active_orders": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "purchase_id": {"type": "integer", "example": 101},
                                        "restaurant_name": {"type": "string", "example": "Cupcake Heaven"},
                                        "listing_title": {"type": "string", "example": "Box of cupcakes"},
                                        "quantity": {"type": "integer", "example": 2},
                                        "total_price": {"type": "string", "example": "25.99"},
                                        "status": {
                                            "type": "string",
                                            "enum": ["PENDING", "ACCEPTED"],
                                            "example": "PENDING"
                                        },
                                        "purchase_date": {
                                            "type": "string",
                                            "format": "date-time",
                                            "example": "2025-01-19T12:34:56"
                                        },
                                        "is_active": {"type": "boolean", "example": True},
                                        "is_delivery": {"type": "boolean", "example": False},
                                        "delivery_address": {"type": "string", "example": None},
                                        "delivery_notes": {"type": "string", "example": None},
                                        "restaurant_details": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer", "example": 5},
                                                "name": {"type": "string", "example": "Cupcake Heaven"},
                                                "image_url": {"type": "string",
                                                              "example": "https://example.com/image.jpg"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "401": {"description": "Unauthorized - Invalid or missing token"},
        "500": {"description": "Internal server error"}
    }
})
def get_user_active_orders():
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        response, status = get_user_active_orders_service(user_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching active orders.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@purchase_bp.route("/user/orders/previous", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Get user's previous orders",
    "description": (
            "Retrieves all completed or rejected orders for the current user, with pagination. "
            "Use `page` and `per_page` query parameters to navigate through results."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "page",
            "in": "query",
            "schema": {"type": "integer", "default": 1},
            "required": False,
            "description": "Page number for pagination",
            "example": 1
        },
        {
            "name": "per_page",
            "in": "query",
            "schema": {"type": "integer", "default": 10},
            "required": False,
            "description": "Number of orders per page",
            "example": 10
        }
    ],
    "responses": {
        "200": {
            "description": "Previous orders retrieved successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "orders": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer", "example": 101},
                                        "listing_title": {"type": "string", "example": "Box of cupcakes"},
                                        "quantity": {"type": "integer", "example": 2},
                                        "total_price": {"type": "string", "example": "25.99"},
                                        "status": {
                                            "type": "string",
                                            "enum": ["COMPLETED", "REJECTED"],
                                            "example": "COMPLETED"
                                        },
                                        "purchase_date": {
                                            "type": "string",
                                            "format": "date-time",
                                            "example": "2025-01-19T12:34:56"
                                        },
                                        "is_delivery": {"type": "boolean", "example": False},
                                        "delivery_address": {"type": "string", "example": None},
                                        "delivery_notes": {"type": "string", "example": None},
                                        "completion_image_url": {
                                            "type": "string",
                                            "example": "https://example.com/uploads/order-101.png"
                                        }
                                    }
                                }
                            },
                            "pagination": {
                                "type": "object",
                                "properties": {
                                    "current_page": {"type": "integer", "example": 1},
                                    "total_pages": {"type": "integer", "example": 1},
                                    "per_page": {"type": "integer", "example": 10},
                                    "total_orders": {"type": "integer", "example": 8},
                                    "has_next": {"type": "boolean", "example": False},
                                    "has_prev": {"type": "boolean", "example": False}
                                }
                            }
                        }
                    }
                }
            }
        },
        "401": {"description": "Unauthorized - Invalid or missing token"},
        "500": {"description": "Internal server error"}
    }
})
def get_user_previous_orders():
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        response, status = get_user_previous_orders_service(user_id, page, per_page)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching previous orders.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@purchase_bp.route("/user/orders/<int:purchase_id>", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Get detailed information about a specific order",
    "description": (
            "Retrieves all available details of a given purchase order by its ID, "
            "including listing and restaurant details if any. "
            "Only the user who made the order can access these details."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "purchase_id",
            "in": "path",
            "schema": {"type": "integer"},
            "required": True,
            "description": "ID of the purchase order to retrieve",
            "example": 101
        }
    ],
    "responses": {
        "200": {
            "description": "Order details retrieved successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "order": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "example": 101},
                                    "listing_title": {"type": "string", "example": "Box of cupcakes"},
                                    "quantity": {"type": "integer", "example": 2},
                                    "total_price": {"type": "string", "example": "25.99"},
                                    "status": {
                                        "type": "string",
                                        "enum": ["PENDING", "ACCEPTED", "REJECTED", "COMPLETED"],
                                        "example": "PENDING"
                                    },
                                    "purchase_date": {
                                        "type": "string",
                                        "format": "date-time",
                                        "example": "2025-01-19T12:34:56"
                                    },
                                    "is_active": {"type": "boolean", "example": True},
                                    "is_delivery": {"type": "boolean", "example": False},
                                    "delivery_address": {"type": "string", "example": None},
                                    "delivery_notes": {"type": "string", "example": None},
                                    "completion_image_url": {
                                        "type": "string",
                                        "example": "https://example.com/uploads/order-101.png"
                                    },
                                    "listing": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer", "example": 12},
                                            "title": {"type": "string", "example": "Box of cupcakes"}
                                        }
                                    },
                                    "restaurant": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer", "example": 5},
                                            "restaurantName": {
                                                "type": "string",
                                                "example": "Cupcake Heaven"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "401": {"description": "Unauthorized - Invalid or missing token"},
        "404": {"description": "Order not found or not accessible by the current user"},
        "500": {"description": "Internal server error"}
    }
})
def get_order_details(purchase_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        response, status = get_order_details_service(user_id, purchase_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching order details.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@purchase_bp.route("/purchase/<int:purchase_id>/completion-image", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Purchases"],
    "summary": "Add a completion image to a purchase (file upload)",
    "description": (
            "Allows the restaurant (or user, depending on your business logic) to upload a completion image file "
            "for a previously **ACCEPTED** purchase. This will mark the purchase as **COMPLETED**."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "purchase_id",
            "in": "path",
            "required": True,
            "schema": {"type": "integer"},
            "description": "ID of the purchase order",
            "example": 101
        }
    ],
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "file": {
                            "type": "string",
                            "format": "binary",
                            "description": "The image file to upload"
                        }
                    },
                    "required": ["file"]
                }
            }
        }
    },
    "responses": {
        "200": {
            "description": "Successfully added completion image and updated the purchase to COMPLETED",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "example": "Completion image added successfully"},
                            "purchase": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "example": 101},
                                    "completion_image_url": {
                                        "type": "string",
                                        "example": "https://example.com/uploads/order-101.png"
                                    },
                                    "status": {
                                        "type": "string",
                                        "enum": ["COMPLETED"],
                                        "example": "COMPLETED"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Purchase must be in ACCEPTED state (or other validation error)."
        },
        "403": {
            "description": "Forbidden - Current user is not authorized (e.g., not the restaurant owner)."
        },
        "404": {
            "description": "Purchase not found."
        },
        "500": {
            "description": "Internal server error."
        }
    }
})
def add_completion_image(purchase_id):
    """
    Example of how to handle file uploads in Flask.
    """
    try:
        # Log the request excluding the binary file to keep logs reasonable
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "files": [k for k in request.files.keys()]
        }
        print(json.dumps({"request": request_log}, indent=2))

        # Current user/owner ID
        owner_id = get_jwt_identity()

        # Retrieve file object from request (under the key 'file')
        file_obj = request.files.get('file')

        if not file_obj:
            error_response = {"message": "No file provided"}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        # Pass the file to your service layer or handle it directly here
        # Suppose your service is updated to accept `file_obj` instead of `image_url`
        from src.services.purchase_service import add_completion_image_service

        response, status = add_completion_image_service(
            purchase_id=purchase_id,
            owner_id=owner_id,
            file_obj=file_obj,
            url_for_func=url_for  # <-- pass Flask's url_for here
        )

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while uploading the completion image.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500