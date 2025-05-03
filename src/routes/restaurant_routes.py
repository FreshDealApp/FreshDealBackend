import os
from datetime import datetime, UTC
import json
import traceback
import sys

from flask import Blueprint, request, jsonify, url_for, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from src.services.restaurant_comment_service import add_comment_service
from src.services.restaurant_service import (
    create_restaurant_service,
    get_restaurants_service,
    get_restaurant_service,
    delete_restaurant_service,
    get_restaurants_proximity_service,
)
from src.models import User, RestaurantComment

restaurant_bp = Blueprint("restaurant", __name__)

# Define upload folder (should match the one in the service layer)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@restaurant_bp.route("/restaurants", methods=["POST"])
@jwt_required()
def create_restaurant():
    """
    Create a new restaurant.

    Expects multipart/form-data with fields:
      - restaurantName (string, required)
      - restaurantDescription (string)
      - longitude (number, required)
      - latitude (number, required)
      - category (string, required)
      - workingDays (multiple values or comma‑separated string)
      - workingHoursStart (string)
      - workingHoursEnd (string)
      - listings (integer)
      - pickup ("true"/"false")
      - delivery ("true"/"false")
      - maxDeliveryDistance (number)
      - deliveryFee (number)
      - minOrderAmount (number)
      - image (file, optional)

    ---
    tags:
      - Restaurant
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            required:
              - restaurantName
              - longitude
              - latitude
              - category
            properties:
              restaurantName:
                type: string
              restaurantDescription:
                type: string
              longitude:
                type: number
              latitude:
                type: number
              category:
                type: string
              workingDays:
                type: array
                items:
                  type: string
              workingHoursStart:
                type: string
              workingHoursEnd:
                type: string
              listings:
                type: integer
                default: 0
              pickup:
                type: string
                enum: [true, false]
              delivery:
                type: string
                enum: [true, false]
              maxDeliveryDistance:
                type: number
              deliveryFee:
                type: number
              minOrderAmount:
                type: number
              image:
                type: string
                format: binary
    responses:
      201:
        description: Restaurant added successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                message:
                  type: string
                restaurant:
                  type: object
      400:
        description: Invalid input.
      403:
        description: Forbidden.
      404:
        description: Owner not found.
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "form": dict(request.form)
        }
        print(json.dumps({"request": request_log}, indent=2))

        owner_id = get_jwt_identity()
        # Optionally, verify owner exists and has role "owner"
        owner = User.query.get(owner_id)
        if not owner:
            error_response = {"success": False, "message": "Owner not found"}
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        if owner.role != "owner":
            error_response = {"success": False, "message": "Only owners can add a restaurant"}
            print(json.dumps({"error_response": error_response, "status": 403}, indent=2))
            return jsonify(error_response), 403

        response, status = create_restaurant_service(owner_id, request.form, request.files, url_for)
        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status

    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@restaurant_bp.route("/restaurants", methods=["GET"])
@jwt_required()
def get_restaurants():
    """
    Get all restaurants for the authenticated owner.

    ---
    tags:
      - Restaurant
    security:
      - BearerAuth: []
    responses:
      200:
        description: A list of restaurants.
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
      404:
        description: No restaurant found for the owner.
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

        owner_id = get_jwt_identity()
        response, status = get_restaurants_service(owner_id)
        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@restaurant_bp.route("/restaurants/<int:restaurant_id>", methods=["GET"])
def get_restaurant(restaurant_id):
    """
    Get a single restaurant by ID.

    ---
    tags:
      - Restaurant
    parameters:
      - in: path
        name: restaurant_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Restaurant details.
      404:
        description: Restaurant not found.
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

        response, status = get_restaurant_service(restaurant_id)
        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@restaurant_bp.route("/restaurants/<int:restaurant_id>", methods=["DELETE"])
@jwt_required()
def delete_restaurant(restaurant_id):
    """
    Delete a restaurant.

    ---
    tags:
      - Restaurant
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: restaurant_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Restaurant successfully deleted.
      403:
        description: Not the owner.
      404:
        description: Restaurant or owner not found.
      500:
        description: An error occurred.
    """
    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    current_user = get_jwt_identity()

    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "timestamp": current_time,
            "user_id": current_user
        }
        print(json.dumps({"request": request_log}, indent=2))

        print(f"[{current_time}] User {current_user} attempting to delete restaurant {restaurant_id}")

        # Verify user exists and is an owner
        owner = User.query.get(current_user)
        if not owner:
            print(f"[{current_time}] User {current_user} not found")
            error_response = {
                "success": False,
                "message": "Owner not found",
                "timestamp": current_time
            }
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        if owner.role != "owner":
            print(f"[{current_time}] User {current_user} attempted to delete restaurant but is not an owner")
            error_response = {
                "success": False,
                "message": "Only owners can delete restaurants",
                "timestamp": current_time
            }
            print(json.dumps({"error_response": error_response, "status": 403}, indent=2))
            return jsonify(error_response), 403

        # Call the service layer
        response, status = delete_restaurant_service(restaurant_id, current_user)

        # Log the result
        if status == 200:
            print(f"[{current_time}] User {current_user} successfully deleted restaurant {restaurant_id}")
        else:
            print(f"[{current_time}] User {current_user} failed to delete restaurant {restaurant_id}. Status: {status}")

        # Add timestamp to response if not present
        if isinstance(response, dict) and "timestamp" not in response:
            response["timestamp"] = current_time

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status

    except Exception as e:
        error_message = f"Error during restaurant deletion: {str(e)}"
        print(f"[{current_time}] User {current_user}: {error_message}")

        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred during restaurant deletion",
            "error": str(e),
            "timestamp": current_time
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@restaurant_bp.route("/uploads/<filename>", methods=['GET'])
def get_uploaded_file(filename):
    """
    Serve an uploaded file.

    ---
    tags:
      - Restaurant
    parameters:
      - in: path
        name: filename
        required: true
        schema:
          type: string
    responses:
      200:
        description: The requested file.
      404:
        description: File not found.
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        filename = secure_filename(filename)
        response = send_from_directory(UPLOAD_FOLDER, filename)
        print(json.dumps({"response": "File served successfully", "filename": filename}, indent=2))
        return response
    except FileNotFoundError:
        error_response = {"success": False, "message": "File not found"}
        print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
        return jsonify(error_response), 404
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@restaurant_bp.route("/restaurants/proximity", methods=["POST"])
@jwt_required()  # Optional: remove if not needed
def get_restaurants_proximity():
    """
    Get restaurants by proximity.

    Expects a JSON payload:
    {
       "latitude": number (required),
       "longitude": number (required),
       "radius": number (optional, default 10 km)
    }

    ---
    tags:
      - Restaurant
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - latitude
              - longitude
            properties:
              latitude:
                type: number
              longitude:
                type: number
              radius:
                type: number
                default: 10
    responses:
      200:
        description: Restaurants within the specified radius.
      400:
        description: Missing or invalid parameters.
      404:
        description: No restaurants found.
      500:
        description: An error occurred.
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "json": request.get_json()
        }
        print(json.dumps({"request": request_log}, indent=2))

        data = request.get_json()
        user_lat = data.get('latitude')
        user_lon = data.get('longitude')
        radius = data.get('radius', 10)
        response, status = get_restaurants_proximity_service(user_lat, user_lon, radius)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@restaurant_bp.route("/restaurants/<int:restaurant_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(restaurant_id):
    """
    Add a comment with optional badge awards to a restaurant.

    This endpoint enables an authenticated user to submit a comment along with a rating for a restaurant.
    The request payload must include:
      - **comment**: The text of the comment.
      - **rating**: The rating value (between 0 and 5).
      - **purchase_id**: The identifier of the purchase related to this comment.

    Additionally, the payload may include:
      - **badge_names**: An array of badge names to award the restaurant.
        Valid badge names are:
        - Positive: `fresh`, `fast_delivery`, `customer_friendly`
        - Negative: `not_fresh`, `slow_delivery`, `not_customer_friendly`

    ---
    summary: Add a comment with optional badge awards for a restaurant.
    description: >
      Submit a comment and rating for a restaurant. Optionally, award one or more badge points to the restaurant
      by providing an array of badge names in the **badge_names** field. Each badge in the array will trigger the
      corresponding badge point award. Both positive and negative badges can be awarded.
    tags:
      - Restaurant
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: restaurant_id
        required: true
        schema:
          type: integer
        description: Unique ID of the restaurant to comment on.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - comment
              - rating
              - purchase_id
            properties:
              comment:
                type: string
                description: The text content of the comment.
              rating:
                type: number
                description: The rating given by the user (must be between 0 and 5).
                minimum: 0
                maximum: 5
              purchase_id:
                type: integer
                description: The ID of the purchase associated with this comment.
              badge_names:
                type: array
                description: >
                  (Optional) An array of badge names to award the restaurant. Each badge name must be one of:
                  Positive badges: `fresh`, `fast_delivery`, `customer_friendly`
                  Negative badges: `not_fresh`, `slow_delivery`, `not_customer_friendly`
                items:
                  type: string
                  enum:
                    - fresh
                    - fast_delivery
                    - customer_friendly
                    - not_fresh
                    - slow_delivery
                    - not_customer_friendly
          examples:
            CommentWithPositiveBadges:
              summary: Submit a comment with positive badge awards.
              value:
                comment: "Great service and delicious food!"
                rating: 4.5
                purchase_id: 123
                badge_names:
                  - fresh
                  - customer_friendly
            CommentWithNegativeBadges:
              summary: Submit a comment with negative badge awards.
              value:
                comment: "Cold food and slow delivery"
                rating: 2.0
                purchase_id: 124
                badge_names:
                  - not_fresh
                  - slow_delivery
            CommentWithoutBadges:
              summary: Submit a comment without awarding any badges.
              value:
                comment: "Average experience"
                rating: 3.0
                purchase_id: 125
    responses:
      201:
        description: Comment added successfully.
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
                  example: "Comment added successfully"
      400:
        description: Missing or invalid input.
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
                  example: "Comment text is required"
      403:
        description: Forbidden (e.g., invalid purchase or duplicate comment).
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
                  example: "No valid purchase found for the user"
      500:
        description: An error occurred during comment submission.
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
                  example: "An error occurred"
                error:
                  type: string
                  example: "Detailed error message"
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "json": request.get_json()
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        data = request.get_json()
        response, status = add_comment_service(restaurant_id, user_id, data)

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
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@restaurant_bp.route("/restaurants/<int:restaurant_id>/comments", methods=["GET"])
def get_restaurant_comments(restaurant_id):
    """
    Get all comments with badges for a restaurant.

    ---
    tags:
      - Restaurant
    parameters:
      - in: path
        name: restaurant_id
        required: true
        schema:
          type: integer
        description: Unique ID of the restaurant to get comments for.
    responses:
      200:
        description: Comments retrieved successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                restaurant_id:
                  type: integer
                  description: The ID of the restaurant
                comments:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        description: Comment ID
                      user_id:
                        type: integer
                        description: ID of the user who made the comment
                      comment:
                        type: string
                        description: The comment text
                      rating:
                        type: number
                        format: float
                        description: Rating given (0-5)
                      timestamp:
                        type: string
                        format: date-time
                        description: When the comment was made
                      badges:
                        type: array
                        items:
                          type: object
                          properties:
                            name:
                              type: string
                              description: Badge name
                            is_positive:
                              type: boolean
                              description: Whether this is a positive or negative badge
            example:
              success: true
              restaurant_id: 123
              comments:
                - id: 1
                  user_id: 456
                  comment: "Great food!"
                  rating: 4.5
                  timestamp: "2025-04-17T21:27:31"
                  badges:
                    - name: "fresh"
                      is_positive: true
                    - name: "fast_delivery"
                      is_positive: true
      500:
        description: An error occurred while retrieving comments.
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
                error:
                  type: string
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        comments = RestaurantComment.query.filter_by(restaurant_id=restaurant_id).all()
        comments_data = []

        for comment in comments:
            badges_data = [{"name": badge.badge_name, "is_positive": badge.is_positive} for badge in comment.badges]

            comment_data = {
                "id": comment.id,
                "user_id": comment.user_id,
                "comment": comment.comment,
                "rating": float(comment.rating),
                "timestamp": comment.timestamp.isoformat(),
                "badges": badges_data
            }
            comments_data.append(comment_data)

        response = {
            "success": True,
            "restaurant_id": restaurant_id,
            "comments": comments_data
        }

        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while retrieving comments",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@restaurant_bp.route("/restaurants/<int:restaurant_id>", methods=["PUT"])
@jwt_required()
def update_restaurant(restaurant_id):
    """
    Update an existing restaurant by its ID.

    Expects multipart/form-data with fields (all optional except what you require):
      - restaurantName (string)
      - restaurantDescription (string)
      - longitude (number)
      - latitude (number)
      - category (string)
      - workingDays (multiple values or comma‑separated string)
      - workingHoursStart (string)
      - workingHoursEnd (string)
      - listings (integer)
      - pickup ("true"/"false")
      - delivery ("true"/"false")
      - maxDeliveryDistance (number)
      - deliveryFee (number)
      - minOrderAmount (number)
      - image (file)

    ---
    tags:
      - Restaurant
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: restaurant_id
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              restaurantName:
                type: string
              restaurantDescription:
                type: string
              longitude:
                type: number
              latitude:
                type: number
              category:
                type: string
              workingDays:
                type: array
                items:
                  type: string
              workingHoursStart:
                type: string
              workingHoursEnd:
                type: string
              listings:
                type: integer
              pickup:
                type: string
                enum: [true, false]
              delivery:
                type: string
                enum: [true, false]
              maxDeliveryDistance:
                type: number
              deliveryFee:
                type: number
              minOrderAmount:
                type: number
              image:
                type: string
                format: binary
    responses:
      200:
        description: Restaurant updated successfully.
      400:
        description: Invalid input.
      403:
        description: Forbidden.
      404:
        description: Restaurant not found.
      500:
        description: An error occurred.
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "form": dict(request.form)
        }
        print(json.dumps({"request": request_log}, indent=2))

        owner_id = get_jwt_identity()

        # (Optionally, verify the user is an owner)
        owner = User.query.get(owner_id)
        if not owner:
            error_response = {"success": False, "message": "Owner not found"}
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        if owner.role != "owner":
            error_response = {"success": False, "message": "Only owners can update a restaurant"}
            print(json.dumps({"error_response": error_response, "status": 403}, indent=2))
            return jsonify(error_response), 403

        from src.services.restaurant_service import update_restaurant_service
        response, status = update_restaurant_service(
            restaurant_id,
            owner_id,
            request.form,
            request.files,
            url_for
        )

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status

    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500