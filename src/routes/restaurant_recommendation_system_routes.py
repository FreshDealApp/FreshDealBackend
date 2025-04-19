from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from flasgger import swag_from
from src.services.restaurant_recommendation_system_service import RestaurantRecommendationSystemService

restaurant_recommendation_bp = Blueprint('restaurant_recommendations', __name__)

@restaurant_recommendation_bp.route('/api/restaurant-recommendations/<int:restaurant_id>', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Restaurant Recommendations"],
    "summary": "Get recommendations for a specific restaurant",
    "description": (
        "Retrieves restaurant-based listing recommendations using collaborative filtering. "
        "Returns listings from other restaurants often co-purchased by users who purchased "
        "from the given restaurant."
    ),
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "restaurant_id",
            "in": "path",
            "schema": {"type": "integer"},
            "required": True,
            "description": "ID of the restaurant to get recommendations for",
            "example": 10
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
                                    "restaurant": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer", "example": 10},
                                            "name": {"type": "string", "example": "Sushi House"}
                                        }
                                    },
                                    "recommendations": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "listing_id": {"type": "integer", "example": 203},
                                                "title": {"type": "string", "example": "Dragon Roll"},
                                                "restaurant_name": {"type": "string", "example": "Tokyo Bites"},
                                                "similarity_score": {"type": "number", "example": 0.76},
                                                "pick_up_price": {"type": "number", "example": 18.99},
                                                "delivery_price": {"type": "number", "example": 22.99}
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
            "description": "Unauthorized",
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
            "description": "Restaurant not found or no recommendations available",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": False},
                            "message": {"type": "string", "example": "Restaurant not found"}
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
def get_restaurant_recommendations(restaurant_id):
    response, status = RestaurantRecommendationSystemService.get_recommendations_for_restaurant(restaurant_id)
    return jsonify(response), status
