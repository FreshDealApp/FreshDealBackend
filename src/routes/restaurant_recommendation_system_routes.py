# src/routes/restaurant_recommendation_system_routes.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from flasgger import swag_from
from src.services.restaurant_recommendation_system_service import RestaurantRecommendationSystemService

# Define the blueprint for recommendations
recommendation_bp = Blueprint('recommendations', __name__)

# Endpoint for initializing the recommendation system
@recommendation_bp.route('/api/initialize_recommendation_system', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Restaurant Recommendations"],
    "summary": "Initialize the Restaurant Recommendation System",
    "description": "This endpoint initializes the recommendation system by processing all completed purchases. "
                   "Once initialized, the system can be used to generate recommendations.",
    "security": [{"BearerAuth": []}],
    "responses": {
        "200": {
            "description": "Recommendation system initialized successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "message": {"type": "string", "example": "Recommendation system initialized"}
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
                            "message": {"type": "string", "example": "Error initializing recommendation system"}
                        }
                    }
                }
            }
        }
    }
})
def initialize_recommendation_system():
    service = RestaurantRecommendationSystemService()
    if service.initialize_model():
        return jsonify({"success": True, "message": "Recommendation system initialized"}), 200
    else:
        return jsonify({"success": False, "message": "Error initializing recommendation system"}), 500

# Endpoint for getting recommendations for a specific user
@recommendation_bp.route('/api/recommendations/<int:user_id>', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Restaurant Recommendations"],
    "summary": "Get restaurant recommendations based on user's purchase history",
    "description": "Retrieves restaurant recommendations based on the user's past purchase history. "
                   "The recommendations are filtered by the category of restaurants in the user's purchase history. "
                   "The original restaurant is excluded from the recommendations.",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "user_id",
            "in": "path",
            "schema": {"type": "integer"},
            "required": True,
            "description": "ID of the user to get recommendations for",
            "example": 101
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
                                    "user_id": {"type": "integer", "example": 101},
                                    "recommendations": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "restaurant_id": {"type": "integer", "example": 202},
                                                "restaurant_name": {"type": "string", "example": "Pizza Palace"},
                                                "category": {"type": "string", "example": "Italian"}
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
            "description": "User not found or no recommendations available",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": False},
                            "message": {"type": "string", "example": "User has no purchases"}
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
def get_recommendations_for_user(user_id):
    response, status = RestaurantRecommendationSystemService.get_recommendations_for_user(user_id)
    return jsonify(response), status
