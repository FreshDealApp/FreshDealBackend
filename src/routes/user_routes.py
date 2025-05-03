import re
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import traceback
import sys

from src.services.purchase_service import get_user_active_orders_service
from src.services.user_service import (
    fetch_user_data,
    change_password,
    change_username,
    change_email,
    add_favorite,
    remove_favorite,
    get_favorites, get_user_recent_restaurants_service
)

user_bp = Blueprint("user", __name__)


def is_valid_email(email):
    """
    Validates an email address using a regex pattern.
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


# ----------------------------
# User Resource
# ----------------------------

@user_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user():
    """
    Get the authenticated user's information and associated addresses.
    ---
    tags:
      - User
    security:
      - BearerAuth: []
    responses:
      200:
        description: User data fetched successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                user_data:
                  type: object
                  properties:
                    id:
                      type: integer
                    name:
                      type: string
                    email:
                      type: string
                    phone_number:
                      type: string
                    role:
                      type: string
                    email_verified:
                      type: boolean
                user_address_list:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      title:
                        type: string
                      longitude:
                        type: number
                        format: float
                      latitude:
                        type: number
                        format: float
                      street:
                        type: string
                      neighborhood:
                        type: string
                      district:
                        type: string
                      province:
                        type: string
                      country:
                        type: string
                      postalCode:
                        type: string
                      apartmentNo:
                        type: string
                      doorNo:
                        type: string
                      is_primary:
                        type: boolean
      404:
        description: User not found.
      500:
        description: An error occurred.
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
        data, error = fetch_user_data(user_id)
        if error:
            status_code = 404 if error == "User not found" else 400
            error_response = {"message": error}
            print(json.dumps({"error_response": error_response, "status": status_code}, indent=2))
            return jsonify(error_response), status_code

        print(json.dumps({"response": data, "status": 200}, indent=2))
        return jsonify(data), 200

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


@user_bp.route("/user/password", methods=["PUT"])
@jwt_required()
def update_password():
    """
    Update the user's password.
    Expects a JSON payload with:
      - old_password: the current password
      - new_password: the new password to set
    ---
    tags:
      - User
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - old_password
              - new_password
            properties:
              old_password:
                type: string
              new_password:
                type: string
    responses:
      200:
        description: Password updated successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      400:
        description: Validation error or incorrect old password.
      500:
        description: An error occurred.
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
        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if not old_password or not new_password:
            error_response = {"message": "Old and new passwords are required"}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        user_id = get_jwt_identity()
        success, message = change_password(user_id, old_password, new_password)
        if not success:
            error_response = {"message": message}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        response = {"message": message}
        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200

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


@user_bp.route("/user/username", methods=["PUT"])
@jwt_required()
def update_username():
    """
    Update the user's username.
    Expects a JSON payload with:
      - username: the new username
    ---
    tags:
      - User
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - username
            properties:
              username:
                type: string
    responses:
      200:
        description: Username updated successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      400:
        description: New username is required.
      404:
        description: User not found.
      500:
        description: An error occurred.
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
        new_username = data.get("username")

        if not new_username:
            error_response = {"message": "New username is required"}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        user_id = get_jwt_identity()
        success, message = change_username(user_id, new_username)
        if not success:
            error_response = {"message": message}
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        response = {"message": message}
        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200

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


@user_bp.route("/user/email", methods=["PUT"])
@jwt_required()
def update_email():
    """
    Update the user's email and send a verification email.
    Expects a JSON payload with:
      - old_email: the current email address
      - new_email: the new email address to update to
    ---
    tags:
      - User
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - old_email
              - new_email
            properties:
              old_email:
                type: string
              new_email:
                type: string
    responses:
      200:
        description: Email updated successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      400:
        description: Validation error or email mismatch.
      500:
        description: An error occurred.
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
        old_email = data.get("old_email")
        new_email = data.get("new_email")

        if not old_email or not new_email:
            error_response = {"message": "Old and new emails are required"}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        # Validate email formats
        if not is_valid_email(old_email):
            error_response = {"message": "Invalid old email format"}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400
        if not is_valid_email(new_email):
            error_response = {"message": "Invalid new email format"}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        user_id = get_jwt_identity()
        success, message = change_email(user_id, old_email, new_email)
        if not success:
            error_response = {"message": message}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        response = {"message": message}
        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200

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


# ----------------------------
# Favorites Sub-Resource
# ----------------------------

@user_bp.route("/user/favorites", methods=["GET"])
@jwt_required()
def get_favorites_route():
    """
    Get the list of favorite restaurants for the authenticated user.
    ---
    tags:
      - Favorites
    security:
      - BearerAuth: []
    responses:
      200:
        description: Favorites retrieved successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                favorites:
                  type: array
                  items:
                    type: integer
      500:
        description: An error occurred.
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
        favorites = get_favorites(user_id)

        response = {"favorites": favorites}
        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200

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


@user_bp.route("/user/favorites", methods=["POST"])
@jwt_required()
def add_favorite_route():
    """
    Add a restaurant to the user's favorites.
    Expects a JSON payload with:
      - restaurant_id: the ID of the restaurant to add
    ---
    tags:
      - Favorites
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - restaurant_id
            properties:
              restaurant_id:
                type: integer
    responses:
      201:
        description: Restaurant added to favorites successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      400:
        description: Validation error.
      500:
        description: An error occurred.
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
        restaurant_id = data.get("restaurant_id")

        if not restaurant_id:
            error_response = {"message": "Restaurant ID is required"}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        user_id = get_jwt_identity()
        success, message = add_favorite(user_id, restaurant_id)
        if not success:
            error_response = {"message": message}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        response = {"message": message}
        print(json.dumps({"response": response, "status": 201}, indent=2))
        return jsonify(response), 201

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


@user_bp.route("/user/favorites", methods=["DELETE"])
@jwt_required()
def remove_favorite_route():
    """
    Remove a restaurant from the user's favorites.
    Expects a JSON payload with:
      - restaurant_id: the ID of the restaurant to remove
    ---
    tags:
      - Favorites
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - restaurant_id
            properties:
              restaurant_id:
                type: integer
    responses:
      200:
        description: Restaurant removed from favorites successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      404:
        description: Favorite not found.
      500:
        description: An error occurred.
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
        restaurant_id = data.get("restaurant_id")

        if not restaurant_id:
            error_response = {"message": "Restaurant ID is required"}
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        user_id = get_jwt_identity()
        success, message = remove_favorite(user_id, restaurant_id)
        if not success:
            error_response = {"message": message}
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        response = {"message": message}
        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200

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


@user_bp.route('/users/active-orders', methods=['GET'])
@jwt_required()  # Assuming you're using Flask-JWT-Extended
def get_user_active_orders():
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        current_user_id = get_jwt_identity()  # Get the current user's ID
        response, status = get_user_active_orders_service(current_user_id)

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


@user_bp.route("/user/recent-restaurants", methods=["GET"])
@jwt_required()
def get_recent_restaurants():
    """
    Get User's Recently Ordered Restaurants
    ---
    tags:
      - User
    summary: Get a list of restaurants from user's recent orders
    description: Returns up to 20 most recently ordered restaurants for the authenticated user
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of recently ordered restaurants retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                restaurants:
                  type: array
                  items:
                    type: object
                    properties:
                      restaurant_id:
                        type: integer
                        example: 1
                      restaurant_name:
                        type: string
                        example: "Pizza Place"
                      image_url:
                        type: string
                        example: "http://example.com/image.jpg"
                      last_order_date:
                        type: string
                        format: date-time
                        example: "2025-04-17T23:07:07Z"
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
        response, status = get_user_recent_restaurants_service(user_id)

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