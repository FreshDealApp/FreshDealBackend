from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.gamification_services import (
    get_user_rankings,
    get_single_user_rank,
    get_monthly_user_rankings,
    get_single_user_monthly_rank)

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

@gamification_bp.route("/user/monthly-rankings", methods=["GET"])
@jwt_required()
def get_monthly_user_rankings_route():
    """
    Get user rankings based on discounts earned in the last 30 days.
    ---
    tags:
      - Rankings
    security:
      - BearerAuth: []
    responses:
      200:
        description: Monthly user rankings fetched successfully.
      500:
        description: An error occurred.
    """
    try:
        return get_monthly_user_rankings()
    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({
            "success": False,
            "message": "An error occurred while fetching monthly user rankings",
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

@gamification_bp.route("/user/monthly-rank/<int:user_id>", methods=["GET"])
@jwt_required()
def get_single_user_monthly_rank_route(user_id):
    """
    Get the rank of a specific user based on discounts earned in the last 30 days.
    ---
    tags:
      - Rankings
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The ID of the user to get the monthly rank for
    security:
      - BearerAuth: []
    responses:
      200:
        description: Monthly user rank fetched successfully.
      404:
        description: User not found.
      500:
        description: An error occurred.
    """
    try:
        return get_single_user_monthly_rank(user_id)
    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({
            "success": False,
            "message": "An error occurred while fetching user's monthly rank",
            "error": str(e)
        }), 500