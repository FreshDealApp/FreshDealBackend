from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.cart_service import (
    get_cart_items_service,
    add_to_cart_service,
    update_cart_item_service,
    remove_from_cart_service,
    reset_cart_service  # new service for resetting the cart
)
import json
import traceback
import sys

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/cart", methods=["GET"])
@jwt_required()
def get_cart_items():
    """
    Get Current User's Cart Items
    ---
    tags:
      - Cart
    summary: Retrieve all items in the current user's shopping cart
    description: Returns a list of all items currently in the authenticated user's shopping cart, including details such as quantity and price.
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successfully retrieved cart items
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                cart:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        description: Cart item ID
                        example: 1
                      listing_id:
                        type: integer
                        description: ID of the listed item
                        example: 123
                      title:
                        type: string
                        description: Name of the item
                        example: "Delicious Pizza"
                      count:
                        type: integer
                        description: Quantity of items in cart
                        example: 2
                      added_at:
                        type: string
                        format: date-time
                        description: Timestamp when item was added to cart
                        example: "2025-01-15T15:10:16Z"
      401:
        description: Authentication required
      500:
        description: Internal server error
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        cart, status = get_cart_items_service(user_id)

        response = {"success": True, "cart": cart}
        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@cart_bp.route("/cart", methods=["POST"])
@jwt_required()
def add_to_cart():
    """
    Add Item to Cart
    ---
    tags:
      - Cart
    summary: Add a new item to the shopping cart
    description: |
      Adds a specified quantity of an item to the user's cart.
      If the item already exists in the cart, the quantity will be updated.
      Ensures that all items in the cart belong to the same restaurant.
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - listing_id
            properties:
              listing_id:
                type: integer
                description: ID of the listing to add to cart
                example: 123
              count:
                type: integer
                description: Quantity to add (defaults to 1)
                default: 1
                minimum: 1
                example: 2
    responses:
      201:
        description: Item successfully added to cart
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Item added to cart"
      400:
        description: Invalid request, insufficient stock, or items in cart belong to a different restaurant
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: false
                message:
                  type: string
                  example: "Cannot add item from a different restaurant"
      401:
        description: Authentication required
      404:
        description: Listing not found
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "body": request.get_json()
        }
        print(json.dumps({"request": request_log}, indent=2))

        data = request.get_json()
        if not data:
            error_response = {
                "success": False,
                "message": "No JSON data provided"
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        listing_id = data.get("listing_id")
        if not listing_id:
            error_response = {
                "success": False,
                "message": "listing_id is required"
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        count = data.get("count", 1)
        user_id = get_jwt_identity()

        response, status = add_to_cart_service(user_id, listing_id, count)
        response_with_success = {**response, "success": status == 201}

        print(json.dumps({"response": response_with_success, "status": status}, indent=2))
        return jsonify(response_with_success), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@cart_bp.route("/cart", methods=["PUT"])
@jwt_required()
def update_cart_item():
    """
    Update Cart Item Quantity
    ---
    tags:
      - Cart
    summary: Update the quantity of an item in the cart
    description: |
      Updates the quantity of a specific item in the user's cart.
      Validates stock availability before updating.
      Use count=0 to effectively remove the item from cart.
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - listing_id
              - count
            properties:
              listing_id:
                type: integer
                description: ID of the listing to update
                example: 123
              count:
                type: integer
                description: New quantity for the item
                minimum: 0
                example: 3
    responses:
      200:
        description: Cart item successfully updated
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Cart item updated"
      400:
        description: Invalid request or insufficient stock
      401:
        description: Authentication required
      404:
        description: Item not found in cart
      500:
        description: Internal server error
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "body": request.get_json()
        }
        print(json.dumps({"request": request_log}, indent=2))

        data = request.get_json()
        if not data:
            error_response = {
                "success": False,
                "message": "No JSON data provided"
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        listing_id = data.get("listing_id")
        count = data.get("count")

        if not listing_id or count is None:
            error_response = {
                "success": False,
                "message": "listing_id and count are required"
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        user_id = get_jwt_identity()
        response, status = update_cart_item_service(user_id, listing_id, count)
        response_with_success = {**response, "success": status == 200}

        print(json.dumps({"response": response_with_success, "status": status}, indent=2))
        return jsonify(response_with_success), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@cart_bp.route("/cart/<int:listing_id>", methods=["DELETE"])
@jwt_required()
def remove_from_cart(listing_id):
    """
    Remove Item from Cart
    ---
    tags:
      - Cart
    summary: Remove an item from the shopping cart
    description: Completely removes a specific item from the user's cart regardless of quantity.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: listing_id
        required: true
        schema:
          type: integer
        description: The ID of the listing to remove from cart
        example: 123
    responses:
      200:
        description: Item successfully removed from cart
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Item removed from cart"
      401:
        description: Authentication required
      404:
        description: Item not found in cart
      500:
        description: Internal server error
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        response, status = remove_from_cart_service(user_id, listing_id)
        response_with_success = {**response, "success": status == 200}

        print(json.dumps({"response": response_with_success, "status": status}, indent=2))
        return jsonify(response_with_success), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@cart_bp.route("/cart/reset", methods=["POST"])
@jwt_required()
def reset_cart():
    """
    Reset Cart
    ---
    tags:
      - Cart
    summary: Remove all items from the shopping cart
    description: Empties the user's cart.
    security:
      - BearerAuth: []
    responses:
      200:
        description: Cart successfully reset
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Cart reset successfully"
      401:
        description: Authentication required
      500:
        description: Internal server error
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        response, status = reset_cart_service(user_id)
        response_with_success = {**response, "success": status == 200}

        print(json.dumps({"response": response_with_success, "status": status}, indent=2))
        return jsonify(response_with_success), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500