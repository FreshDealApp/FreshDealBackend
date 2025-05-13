import json
import traceback
import sys

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.services.restaurant_service import get_flash_deals_service

flash_deals_bp = Blueprint("flash_deals", __name__)

@flash_deals_bp.route("/flash-deals", methods=["POST"])
@jwt_required()
def get_flash_deals():
    """
    Get restaurants with flash deals by proximity.

    Expects a JSON payload:
    {
       "latitude": number (required),
       "longitude": number (required),
       "radius": number (optional, default 30 km)
    }

    ---
    tags:
      - Flash Deals
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
                default: 30
    responses:
      200:
        description: Restaurants with flash deals within the specified radius.
      400:
        description: Missing or invalid parameters.
      404:
        description: No restaurants with flash deals found.
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
        radius = data.get('radius', 30)
        response, status = get_flash_deals_service(user_lat, user_lon, radius)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500