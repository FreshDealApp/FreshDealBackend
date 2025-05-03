from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import User, Restaurant
from src.services.analytics_service import RestaurantAnalyticsService
from functools import wraps
import json
import traceback
import sys

analytics_bp = Blueprint('analytics', __name__)


def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'owner':
            error_response = {
                "success": False,
                "message": "This endpoint is only available for restaurant owners"
            }
            print(json.dumps({"error_response": error_response, "status": 403}, indent=2))
            return jsonify(error_response), 403
        return f(*args, **kwargs)

    return decorated_function


@analytics_bp.route('/analytics/dashboard', methods=['GET'])
@jwt_required()
@owner_required
def get_owner_analytics():
    """
    Get analytics dashboard data for all restaurants owned by the authenticated user
    ---
    tags:
      - Analytics
    security:
      - BearerAuth: []
    responses:
      200:
        description: Analytics dashboard data
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
                    monthly_stats:
                      type: object
                      properties:
                        total_products_sold:
                          type: integer
                        total_revenue:
                          type: string
                        period:
                          type: string
                    regional_distribution:
                      type: object
                    restaurant_ratings:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          id:
                            type: integer
                          average_rating:
                            type: number
                          total_ratings:
                            type: integer
                          recent_comments:
                            type: array
                            items:
                              type: object
                              properties:
                                user_name:
                                  type: string
                                rating:
                                  type: number
                                comment:
                                  type: string
                                timestamp:
                                  type: string
      403:
        description: User is not a restaurant owner
      404:
        description: No restaurants found for this owner
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
        response, status_code = RestaurantAnalyticsService.get_owner_analytics(owner_id)

        print(json.dumps({"response": response, "status": status_code}, indent=2))
        return jsonify(response), status_code
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching owner analytics data.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@analytics_bp.route('/analytics/restaurants/<int:restaurant_id>', methods=['GET'])
@jwt_required()
@owner_required
def get_restaurant_analytics(restaurant_id):
    """
    Get analytics dashboard data for a specific restaurant
    ---
    tags:
      - Analytics
    security:
      - BearerAuth: []
    parameters:
      - name: restaurant_id
        in: path
        required: true
        schema:
          type: integer
        description: ID of the restaurant to get analytics for
    responses:
      200:
        description: Restaurant analytics data
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
                    monthly_stats:
                      type: object
                      properties:
                        total_products_sold:
                          type: integer
                        total_revenue:
                          type: string
                        period:
                          type: string
                    regional_distribution:
                      type: object
                    restaurant_stats:
                      type: object
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
                        average_rating:
                          type: number
                        total_ratings:
                          type: integer
                        recent_comments:
                          type: array
                          items:
                            type: object
                            properties:
                              user_name:
                                type: string
                              rating:
                                type: number
                              comment:
                                type: string
                              timestamp:
                                type: string
                              badges:
                                type: array
                                items:
                                  type: object
                                  properties:
                                    name:
                                      type: string
                                    is_positive:
                                      type: boolean
      403:
        description: User is not a restaurant owner
      404:
        description: Restaurant not found
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
        restaurant = Restaurant.query.get(restaurant_id)

        if not restaurant:
            error_response = {
                "success": False,
                "message": f"Restaurant with ID {restaurant_id} not found"
            }
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        if str(restaurant.owner_id) != str(owner_id):  # Convert both to strings for comparison
            error_response = {
                "success": False,
                "message": "You don't have permission to view this restaurant's analytics"
            }
            print(json.dumps({"error_response": error_response, "status": 403}, indent=2))
            return jsonify(error_response), 403

        response, status_code = RestaurantAnalyticsService.get_restaurant_analytics(restaurant_id)

        print(json.dumps({"response": response, "status": status_code}, indent=2))
        return jsonify(response), status_code
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately from JSON output
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching restaurant analytics data.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500