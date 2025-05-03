from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.gamification_services import get_user_rankings, get_single_user_rank
import json
import traceback
import sys

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
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        response = get_user_rankings()

        print(json.dumps({"response": response[0], "status": response[1]}, indent=2))
        return response

    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching user rankings",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


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
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        response = get_single_user_rank(user_id)

        print(json.dumps({"response": response[0], "status": response[1]}, indent=2))
        return response
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching user rank",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500