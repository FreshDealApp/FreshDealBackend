from datetime import datetime
from sqlalchemy import func, and_
from src.models import db, Purchase, Listing, Restaurant
from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd

class RestaurantRecommendationSystemService:
    def __init__(self):
        self.purchase_matrix = None
        self.listing_ids = None
        self.model = None
        self.is_initialized = False
        self.k_neighbors = 5

    def initialize_model(self):
        if self.is_initialized:
            return True

        try:
            # Get all completed purchases
            purchases = Purchase.query.filter_by(status='COMPLETED').all()
            if not purchases:
                return False

            # Create purchase data
            purchase_data = []
            for purchase in purchases:
                purchase_data.append({
                    'user_id': purchase.user_id,
                    'listing_id': purchase.listing_id,
                    'quantity': purchase.quantity
                })

            # Convert to DataFrame
            df = pd.DataFrame(purchase_data)

            # Create user-item matrix
            user_listing_matrix = pd.pivot_table(
                data=df,
                index='listing_id',
                columns='user_id',
                values='quantity',
                fill_value=0
            )

            self.purchase_matrix = user_listing_matrix.values
            self.listing_ids = user_listing_matrix.index.tolist()

            # Create KNN model
            self.model = NearestNeighbors(
                n_neighbors=min(self.k_neighbors, len(self.listing_ids)),
                metric='cosine',
                algorithm='brute'
            )
            self.model.fit(self.purchase_matrix)
            self.is_initialized = True
            return True

        except Exception as e:
            print(f"Error initializing model: {e}")
            return False

    @staticmethod
    def get_recommendations_for_user(user_id):
        service = RestaurantRecommendationSystemService()
        if not service.initialize_model():
            return {
                "success": False,
                "message": "Could not initialize recommendation model"
            }, 404

        try:
            # Get the user's purchases
            user_purchases = Purchase.query.filter_by(user_id=user_id).all()
            if not user_purchases:
                return {
                    "success": False,
                    "message": "User has no purchases"
                }, 404

            # Get the restaurant_id and category for each purchase
            restaurant_ids = set()
            for purchase in user_purchases:
                listing = Listing.query.get(purchase.listing_id)
                if listing:
                    restaurant = Restaurant.query.get(listing.restaurant_id)
                    if restaurant:
                        restaurant_ids.add(restaurant.id)

            if not restaurant_ids:
                return {
                    "success": False,
                    "message": "No restaurant found for this user"
                }, 404

            recommendations = []
            for restaurant_id in restaurant_ids:
                restaurant = Restaurant.query.get(restaurant_id)
                if restaurant:
                    category = restaurant.category
                    # Find other restaurants in the same category
                    other_restaurants = Restaurant.query.filter(
                        and_(Restaurant.category == category, Restaurant.id != restaurant_id)
                    ).all()

                    for rec_restaurant in other_restaurants:
                        recommendations.append({
                            "restaurant_id": rec_restaurant.id,
                            "restaurant_name": rec_restaurant.restaurantName,
                            "category": rec_restaurant.category,
                        })

            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "recommendations": recommendations
                }
            }, 200

        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {
                "success": False,
                "message": "Error getting recommendations"
            }, 500
