from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from flasgger import swag_from
from src.services.recommendation_system_service import RecommendationSystemService
import json
import traceback
import sys

recommendation_bp = Blueprint('recommendations', __name__)


@recommendation_bp.route('/api/recommendations/<int:listing_id>', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Recommendations"],
    "summary": "Get recommendations for a specific listing",
    "description": (
            "Retrieves personalized recommendations for a given listing based on purchase patterns "
            "using a KNN-based collaborative filtering approach. The recommendations are sorted "
            "by similarity score."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "listing_id",
            "in": "path",
            "schema": {"type": "integer"},
            "required": True,
            "description": "ID of the listing to get recommendations for",
            "example": 51
        }
    ],
    "responses": {
        "200": {
            "description": "Recommendations retrieved successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "data": {
                                "type": "object",
                                "properties": {
                                    "listing": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer", "example": 101},
                                            "title": {"type": "string", "example": "Veggie Pizza"}
                                        }
                                    },
                                    "recommendations": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "listing_id": {"type": "integer", "example": 102},
                                                "title": {"type": "string", "example": "Margherita Pizza"},
                                                "restaurant_name": {"type": "string", "example": "Pizza Palace"},
                                                "similarity_score": {"type": "number", "example": 0.85},
                                                "pick_up_price": {"type": "number", "example": 12.99},
                                                "delivery_price": {"type": "number", "example": 15.99}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized - Missing or invalid authorization token",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "msg": {"type": "string", "example": "Missing Authorization Header"}
                        }
                    }
                }
            }
        },
        "404": {
            "description": "Listing not found or no recommendations available",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": False},
                            "message": {"type": "string", "example": "Listing not found"}
                        }
                    }
                }
            }
        },
        "500": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": False},
                            "message": {"type": "string", "example": "Error getting recommendations"}
                        }
                    }
                }
            }
        }
    }
})
def get_recommendations_for_listing(listing_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        response, status = RecommendationSystemService.get_recommendations_for_listing(listing_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching recommendations",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500