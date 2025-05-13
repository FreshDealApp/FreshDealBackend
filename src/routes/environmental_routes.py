from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.environmental_service import EnvironmentalService
import json
import traceback
import sys

environmental_bp = Blueprint('environmental', __name__)


@environmental_bp.route('/environmental/contributions', methods=['GET'])
@jwt_required()
def get_user_environmental_contributions():
    """
    Get the environmental contribution (CO2 avoided) for the authenticated user
    ---
    tags:
      - Environmental
    security:
      - BearerAuth: []
    responses:
      200:
        description: Environmental contribution data
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: object
                  properties:
                    total_co2_avoided:
                      type: number
                      description: Total CO2 avoided by the user (kg CO2 equivalent)
                    monthly_co2_avoided:
                      type: number
                      description: CO2 avoided in the last month (kg CO2 equivalent)
                    unit:
                      type: string
                      description: Unit of measurement
      401:
        description: Unauthorized - Invalid or missing token
      500:
        description: Internal server error
    """
    try:
        user_id = get_jwt_identity()
        response = EnvironmentalService.get_user_contributions(user_id)
        return jsonify(response), 200
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching environmental contributions.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@environmental_bp.route('/environmental/leaderboard', methods=['GET'])
@jwt_required()
def get_environmental_leaderboard():
    """
    Get the environmental contribution leaderboard for all users
    ---
    tags:
      - Environmental
    security:
      - BearerAuth: []
    responses:
      200:
        description: Environmental contribution leaderboard
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: array
                  items:
                    type: object
                    properties:
                      user_id:
                        type: integer
                      total_co2_avoided:
                        type: number
                      monthly_co2_avoided:
                        type: number
                unit:
                  type: string
      401:
        description: Unauthorized - Invalid or missing token
      500:
        description: Internal server error
    """
    try:
        response = EnvironmentalService.get_all_users_contributions()
        return jsonify(response), 200
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching environmental leaderboard.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500