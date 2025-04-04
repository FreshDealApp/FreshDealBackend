from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.gamification_services import get_user_rankings, get_single_user_rank, get_restaurant_badges, add_restaurant_badge_point

gamification_bp = Blueprint("gamification", __name__)


@gamification_bp.route("/user/rankings", methods=["GET"])
@jwt_required()
def get_user_rankings_route():
    """
    Get the user rankings based on total discounts earned.
    ---
    tags:
      - Rankings
    security:
      - BearerAuth: []
    responses:
      200:
        description: User rankings fetched successfully.
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  rank:
                    type: integer
                  user_id:
                    type: integer
                  user_name:
                    type: string
                  total_discount:
                    type: number
                    format: float
      500:
        description: An error occurred.
    """
    try:
        return get_user_rankings()

    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({
            "success": False,
            "message": "An error occurred while fetching user rankings",
            "error": str(e)
        }), 500

@gamification_bp.route("/user/rank/<int:user_id>", methods=["GET"])
@jwt_required()
def get_single_user_rank_route(user_id):
    """
    Get the rank of a specific user based on their total discount earned.
    ---
    tags:
      - Rankings
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The ID of the user whose rank we want to find
    security:
      - BearerAuth: []
    responses:
      200:
        description: User rank fetched successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: integer
                  description: The user's ID
                user_name:
                  type: string
                  description: The user's name
                rank:
                  type: integer
                  description: The user's current rank
                total_discount:
                  type: number
                  format: float
                  description: Total discount amount earned by the user
      404:
        description: User not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: User not found
      500:
        description: An error occurred.
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
                  example: An error occurred while fetching user rank
                error:
                  type: string
    """
    try:
        return get_single_user_rank(user_id)
    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({
            "success": False,
            "message": "An error occurred while fetching user rank",
            "error": str(e)
        }), 500

# Get Restaurant Badges Endpoint
@gamification_bp.route("/restaurant/<int:restaurant_id>/badges", methods=["GET"])
@jwt_required()
def get_restaurant_badges_route(restaurant_id):
    """
    Get the badges of a specific restaurant based on its badge points.
    ---
    tags:
      - Rankings
    parameters:
      - name: restaurant_id
        in: path
        type: integer
        required: true
        description: The ID of the restaurant whose badges we want to find
    security:
      - BearerAuth: []
    responses:
      200:
        description: Restaurant badges fetched successfully.
        content:
          application/json:
            schema:
              type: array
              items:
                type: string
              example: ["super_fresh", "fast_delivery"]
      404:
        description: Restaurant not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: Restaurant not found
      500:
        description: An error occurred.
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
                  example: An error occurred while fetching restaurant badges
                error:
                  type: string
    """
    try:
        badges = get_restaurant_badges(restaurant_id)
        if not badges:
            return jsonify({"error": "Restaurant not found"}), 404
        return jsonify(badges)
    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({
            "success": False,
            "message": "An error occurred while fetching restaurant badges",
            "error": str(e)
        }), 500

# Add Restaurant Badge Point Endpoint
@gamification_bp.route("/restaurant/<int:restaurant_id>/badge", methods=["POST"])
@jwt_required()
def add_restaurant_badge_point_route(restaurant_id):
    """
    Add or update a badge for a specific restaurant.
    ---
    tags:
      - Rankings
    parameters:
      - name: restaurant_id
        in: path
        type: integer
        required: true
        description: The ID of the restaurant to which the badge will be added
      - name: badge_name
        in: body
        type: string
        required: true
        description: The name of the badge to add
        schema:
          type: object
          properties:
            badge_name:
              type: string
              example: 'fast_delivery'
    security:
      - BearerAuth: []
    responses:
      200:
        description: Badge points added or updated successfully.
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
                  example: 'Badge points added successfully.'
      400:
        description: Invalid badge name.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: 'Invalid badge name provided.'
      404:
        description: Restaurant not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: 'Restaurant not found.'
      500:
        description: An error occurred while adding/updating badge points.
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
                  example: 'An error occurred while adding badge points.'
                error:
                  type: string
    """
    try:
        # Extract badge_name from the request body
        data = request.get_json()
        badge_name = data.get('badge_name')

        # Check if badge_name was provided
        if not badge_name:
            return jsonify({
                "success": False,
                "message": "Badge name is required"
            }), 400

        # Call the service function to add the badge point
        add_restaurant_badge_point(restaurant_id, badge_name)

        return jsonify({
            "success": True,
            "message": "Badge points added successfully."
        })

    except ValueError as ve:
        return jsonify({
            "success": False,
            "message": "Invalid badge name provided.",
            "error": str(ve)
        }), 400
    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({
            "success": False,
            "message": "An error occurred while adding badge points.",
            "error": str(e)
        }), 500