from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.services.restaurant_badge_services import get_restaurant_badges, add_restaurant_badge_point, VALID_BADGES, \
    get_restaurant_badge_analytics
import json
import traceback
import sys

restaurant_badge_bp = Blueprint("restaurant_badge", __name__)


@restaurant_badge_bp.route("/restaurants/<int:restaurant_id>/badges", methods=["GET"])
def get_badges(restaurant_id):
    """
    Retrieve Restaurant Badges and Points
    This endpoint retrieves all badges and their points for a given restaurant.

    ---
    summary: Retrieve badges and points for a restaurant
    description: >
      Returns a JSON object with the restaurant ID and detailed badge points information,
      including both positive and negative badge counts.
    tags:
      - Restaurant Badge
    parameters:
      - name: restaurant_id
        in: path
        type: integer
        required: true
        description: Unique identifier of the restaurant.
    responses:
      200:
        description: Badges retrieved successfully.
        schema:
          type: object
          properties:
            restaurant_id:
              type: integer
              description: The unique ID of the restaurant.
            badge_points:
              type: object
              properties:
                fresh:
                  type: integer
                  description: Points for fresh badge
                not_fresh:
                  type: integer
                  description: Points for not fresh badge
                fast_delivery:
                  type: integer
                  description: Points for fast delivery badge
                slow_delivery:
                  type: integer
                  description: Points for slow delivery badge
                customer_friendly:
                  type: integer
                  description: Points for customer friendly badge
                not_customer_friendly:
                  type: integer
                  description: Points for not customer friendly badge
        examples:
          application/json:
            restaurant_id: 1
            badge_points:
              fresh: 150
              not_fresh: 20
              fast_delivery: 200
              slow_delivery: 30
              customer_friendly: 180
              not_customer_friendly: 25
      500:
        description: An error occurred while retrieving badges.
        schema:
          type: object
          properties:
            success:
              type: boolean
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

        badge_points = get_restaurant_badges(restaurant_id)
        response = {
            "restaurant_id": restaurant_id,
            "badge_points": badge_points
        }

        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while retrieving badges",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@restaurant_badge_bp.route("/restaurants/<int:restaurant_id>/badge-analytics", methods=["GET"])
def get_badge_analytics(restaurant_id):
    """
    Get Restaurant Badge Analytics
    This endpoint retrieves analytics for all badge types for a given restaurant.

    ---
    summary: Get badge analytics for a restaurant
    description: >
      Returns a JSON object containing analytics for all badge categories including
      the count of positive and negative badges for each category.
    tags:
      - Restaurant Badge
    parameters:
      - name: restaurant_id
        in: path
        type: integer
        required: true
        description: Unique identifier of the restaurant
    responses:
      200:
        description: Badge analytics retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            restaurant_id:
              type: integer
              description: The unique ID of the restaurant
            badge_analytics:
              type: object
              properties:
                freshness:
                  type: object
                  properties:
                    fresh:
                      type: integer
                      description: Count of fresh badges
                    not_fresh:
                      type: integer
                      description: Count of not fresh badges
                delivery:
                  type: object
                  properties:
                    fast_delivery:
                      type: integer
                      description: Count of fast delivery badges
                    slow_delivery:
                      type: integer
                      description: Count of slow delivery badges
                customer_service:
                  type: object
                  properties:
                    customer_friendly:
                      type: integer
                      description: Count of customer friendly badges
                    not_customer_friendly:
                      type: integer
                      description: Count of not customer friendly badges
        examples:
          application/json:
            success: true
            restaurant_id: 1
            badge_analytics:
              freshness:
                fresh: 25
                not_fresh: 5
              delivery:
                fast_delivery: 30
                slow_delivery: 8
              customer_service:
                customer_friendly: 40
                not_customer_friendly: 3
      500:
        description: An error occurred while retrieving badge analytics
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

        analytics = get_restaurant_badge_analytics(restaurant_id)
        response = {
            "success": True,
            "restaurant_id": restaurant_id,
            "badge_analytics": analytics
        }

        print(json.dumps({"response": response, "status": 200}, indent=2))
        return jsonify(response), 200
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while retrieving badge analytics",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500