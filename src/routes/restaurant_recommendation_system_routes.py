from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from flasgger import swag_from
from src.services.restaurant_recommendation_system_service import RestaurantRecommendationSystemService

restaurant_recommendation_bp = Blueprint('restaurant_recommendations', __name__)

@restaurant_recommendation_bp.route('/api/recommendations/user/<int:user_id>', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Restaurant Recommendations"],
    "summary": "Get restaurant recommendations based on user purchase history",
    "description": (
        "Retrieves restaurant recommendations based on the categories of restaurants from "
        "a user's purchase history using a KNN-based approach. The recommendations are sorted "
        "by similarity score."
    ),
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
                                    "restaurants_from_history": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                        "example": [1, 5, 10]
                                    },
                                    "recommendations": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "restaurant_id": {"type": "integer", "example": 201},
                                                "restaurant_name": {"type": "string", "example": "Pizza Palace"},
                                                "category": {"type": "string", "example": "Italian"},
                                                "similarity_score": {"type": "number", "example": 0.85},
                                                "address": {"type": "string", "example": "123 Main St"},
                                                "based_on": {
                                                    "type": "object",
                                                    "properties": {
                                                        "restaurant_id": {"type": "integer", "example": 1},
                                                        "restaurant_name": {"type": "string", "example": "Pasta Paradise"},
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
            "description": "User not found or no purchase history available",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": False},
                            "message": {"type": "string", "example": "No purchase history found for this user"}
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
    response, status = RestaurantRecommendationSystemService.get_recommendations_by_user(user_id)
    return jsonify(response), status