from datetime import datetime
from sqlalchemy import func, and_
from src.models import db, Purchase, Listing, Restaurant
from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd


class RecommendationSystemService:
    def __init__(self, target_category=None):
        self.purchase_matrix = None
        self.listing_ids = None
        self.model = None
        self.is_initialized = False
        self.k_neighbors = 5
        self.target_category = target_category

    def initialize_model(self):
        if self.is_initialized:
            return True

        try:
            # Filter purchases by status
            purchases = Purchase.query.filter_by(status='COMPLETED').all()
            if not purchases:
                return False

            # Get all listings
            all_listings = Listing.query.all()
            listing_map = {l.id: l for l in all_listings}

            # Get all restaurants for category info
            restaurants = Restaurant.query.all()
            restaurant_map = {r.id: r for r in restaurants}

            # Filter purchase data by category
            purchase_data = []
            for purchase in purchases:
                listing = listing_map.get(purchase.listing_id)
                if listing:
                    # Get restaurant to access category
                    restaurant = restaurant_map.get(listing.restaurant_id)
                    if restaurant and restaurant.category == self.target_category:
                        purchase_data.append({
                            'user_id': purchase.user_id,
                            'listing_id': purchase.listing_id,
                            'quantity': purchase.quantity
                        })

            if not purchase_data:
                return False

            df = pd.DataFrame(purchase_data)

            user_listing_matrix = pd.pivot_table(
                data=df,
                index='listing_id',
                columns='user_id',
                values='quantity',
                fill_value=0
            )

            self.purchase_matrix = user_listing_matrix.values
            self.listing_ids = user_listing_matrix.index.tolist()

            self.model = NearestNeighbors(
                n_neighbors=min(self.k_neighbors + 1, len(self.listing_ids)),
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
        # First, get the Listing object
        target_listing = Listing.query.get(listing_id)
        if not target_listing:
            return {
                "success": False,
                "message": "Listing not found"
            }, 404

        # Access the restaurant_id from the Listing model
        restaurant_id = target_listing.restaurant_id

        # Query the Restaurant model using the restaurant_id
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return {
                "success": False,
                "message": "Restaurant not found"
            }, 404

        # Get the category from the Restaurant model
        category = restaurant.category

        # Check if category is None or invalid
        if not category:
            return {
                "success": False,
                "message": "Restaurant category is missing or invalid"
            }, 500

        # Debug: Print category for confirmation
        print(f"Category retrieved: {category}")

        # Initialize the recommendation system with the category from the restaurant
        service = RecommendationSystemService(target_category=category)

        if not service.initialize_model():
            return {
                "success": False,
                "message": "Could not initialize recommendation model"
            }, 500

        try:
            try:
                listing_idx = service.listing_ids.index(listing_id)
            except ValueError:
                return {
                    "success": False,
                    "message": "Listing not in training data"
                }, 404

            distances, indices = service.model.kneighbors(
                [service.purchase_matrix[listing_idx]],
                n_neighbors=min(service.k_neighbors + 1, len(service.listing_ids))
            )

            similarities = 1 - distances.flatten()

            recommendations = []
            for idx, similarity in zip(indices.flatten(), similarities):
                recommended_id = service.listing_ids[idx]
                if recommended_id == listing_id:
                    continue

                rec_listing = Listing.query.get(recommended_id)
                if rec_listing:
                    restaurant = Restaurant.query.get(rec_listing.restaurant_id)
                    recommendations.append({
                        "listing_id": rec_listing.id,
                        "title": rec_listing.title,
                        "restaurant_name": restaurant.restaurantName if restaurant else "Unknown",
                        # Use restaurantName from model
                        "similarity_score": float(similarity),
                        "pick_up_price": rec_listing.pick_up_price,
                        "delivery_price": rec_listing.delivery_price
                    })

                if len(recommendations) >= service.k_neighbors:
                    break

            return {
                "success": True,
                "data": {
                    "listing": {
                        "id": target_listing.id,
                        "title": target_listing.title
                    },
                    "recommendations": recommendations
                }
            }, 200

        except Exception as e:
            import traceback
            return {
                "success": False,
                "message": "Internal server error",
                "details": traceback.format_exc()
            }, 500