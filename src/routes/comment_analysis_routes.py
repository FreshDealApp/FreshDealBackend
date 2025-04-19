from flask import Blueprint, jsonify
from src.services.recommendation_service import RecommendationSystemService

recommendation_bp = Blueprint("recommendation", __name__)

@recommendation_bp.route("/recommendation/<int:listing_id>", methods=["GET"])
def get_recommendations(listing_id):
    """
    Get KNN-based recommendations for a given listing.

    Returns a list of similar listings based on past purchase behavior using collaborative filtering.

    ---
    tags:
      - Recommendation
    parameters:
      - in: path
        name: listing_id
        required: true
        schema:
          type: integer
        description: ID of the listing to get recommendations for.
    responses:
      200:
        description: Recommendation data returned successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                data:
                  type: object
                  properties:
                    listing:
                      type: object
                      properties:
                        id:
                          type: integer
                          example: 1
                        title:
                          type: string
                          example: "Cheese Toast"
                    recommendations:
                      type: array
                      items:
                        type: object
                        properties:
                          listing_id:
                            type: integer
                            example: 2
                          title:
                            type: string
                            example: "Börek Plate"
                          restaurant_name:
                            type: string
                            example: "DoyDoy"
                          similarity_score:
                            type: number
                            format: float
                            example: 0.82
                          pick_up_price:
                            type: number
                            example: 25.0
                          delivery_price:
                            type: number
                            example: 32.5
      404:
        description: Listing not found or insufficient data to make recommendations.
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
                  example: "Listing not found"
      500:
        description: Internal server error during recommendation generation.
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
                  example: "Error getting recommendations"
    """
    return RecommendationSystemService.get_recommendations_for_listing(listing_id)
