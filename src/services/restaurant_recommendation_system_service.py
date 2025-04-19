from sqlalchemy import and_
from src.models import db, Purchase, Listing, Restaurant
from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd


class RestaurantRecommendationSystemService:
    def __init__(self):
        self.restaurant_matrix = None
        self.restaurant_ids = None
        self.model = None
        self.is_initialized = False
        self.k_neighbors = 5

    def initialize_model(self):
        if self.is_initialized:
            return True

        try:
            purchases = Purchase.query.filter_by(status='COMPLETED').all()
            if not purchases:
                return False

            data = []
            for purchase in purchases:
                listing = Listing.query.get(purchase.listing_id)
                if listing:
                    data.append({
                        'user_id': purchase.user_id,
                        'restaurant_id': listing.restaurant_id,
                        'quantity': purchase.quantity
                    })

            df = pd.DataFrame(data)

            user_restaurant_matrix = pd.pivot_table(
                data=df,
                index='restaurant_id',
                columns='user_id',
                values='quantity',
                fill_value=0
            )

            self.restaurant_matrix = user_restaurant_matrix.values
            self.restaurant_ids = user_restaurant_matrix.index.tolist()

            self.model = NearestNeighbors(
                n_neighbors=min(self.k_neighbors, len(self.restaurant_ids)),
                metric='cosine',
                algorithm='brute'
            )
            self.model.fit(self.restaurant_matrix)
            self.is_initialized = True
            return True

        except Exception as e:
            print(f"Error initializing restaurant model: {e}")
            return False

    @staticmethod
    def get_recommendations_for_restaurant(restaurant_id):
        service = RestaurantRecommendationSystemService()
        if not service.initialize_model():
            return {
                "success": False,
                "message": "Could not initialize restaurant recommendation model"
            }, 404

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return {
                "success": False,
                "message": "Restaurant not found"
            }, 404

        try:
            idx = service.restaurant_ids.index(restaurant_id)
        except ValueError:
            return {
                "success": False,
                "message": "Restaurant not found in training data"
            }, 404

        try:
            distances, indices = service.model.kneighbors(
                [service.restaurant_matrix[idx]],
                n_neighbors=min(service.k_neighbors, len(service.restaurant_ids))
            )
            similarities = 1 - distances.flatten()

            recommendations = []
            for i, similarity in zip(indices.flatten(), similarities):
                other_restaurant_id = service.restaurant_ids[i]
                if other_restaurant_id == restaurant_id:
                    continue

                other_restaurant = Restaurant.query.get(other_restaurant_id)
                if not other_restaurant:
                    continue

                # Get one sample listing from this restaurant
                sample_listing = Listing.query.filter_by(restaurant_id=other_restaurant_id).first()
                if not sample_listing:
                    continue

                recommendations.append({
                    "listing_id": sample_listing.id,
                    "title": sample_listing.title,
                    "restaurant_name": other_restaurant.restaurantName,
                    "similarity_score": float(similarity),
                    "pick_up_price": sample_listing.pick_up_price,
                    "delivery_price": sample_listing.delivery_price
                })

            return {
                "success": True,
                "data": {
                    "restaurant": {
                        "id": restaurant.id,
                        "name": restaurant.restaurantName
                    },
                    "recommendations": recommendations
                }
            }, 200

        except Exception as e:
            print(f"Error getting restaurant recommendations: {e}")
            return {
                "success": False,
                "message": "Error getting recommendations"
            }, 500