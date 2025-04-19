from datetime import datetime
from sqlalchemy import func, and_
from src.models import db, Purchase, Listing, Restaurant
from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd


class RecommendationSystemService:
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
    def get_recommendations_for_listing(listing_id):
        service = RecommendationSystemService()
        if not service.initialize_model():
            return {
                "success": False,
                "message": "Could not initialize recommendation model"
            }, 404

        try:
            # Get the target listing
            listing = Listing.query.get(listing_id)
            if not listing:
                return {
                    "success": False,
                    "message": "Listing not found"
                }, 404

            # Find listing index
            try:
                listing_idx = service.listing_ids.index(listing_id)
            except ValueError:
                return {
                    "success": False,
                    "message": "Listing not found in training data"
                }, 404

            # Get recommendations using KNN
            distances, indices = service.model.kneighbors(
                [service.purchase_matrix[listing_idx]],
                n_neighbors=min(service.k_neighbors, len(service.listing_ids))
            )

            # Convert distances to similarity scores
            similarities = 1 - distances.flatten()

            recommendations = []
            for idx, similarity in zip(indices.flatten(), similarities):
                if service.listing_ids[idx] != listing_id:  # Skip the input listing
                    rec_listing = Listing.query.get(service.listing_ids[idx])
                    if rec_listing:
                        restaurant = Restaurant.query.get(rec_listing.restaurant_id)
                        recommendations.append({
                            "listing_id": rec_listing.id,
                            "title": rec_listing.title,
                            "restaurant_name": restaurant.restaurantName if restaurant else "Unknown",
                            "similarity_score": float(similarity),
                            "pick_up_price": rec_listing.pick_up_price,
                            "delivery_price": rec_listing.delivery_price
                        })

            return {
                "success": True,
                "data": {
                    "listing": {
                        "id": listing.id,
                        "title": listing.title
                    },
                    "recommendations": recommendations
                }
            }, 200

        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {
                "success": False,
                "message": "Error getting recommendations"
            }, 500