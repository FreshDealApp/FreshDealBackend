from datetime import datetime
from sqlalchemy import func, and_
from src.models import db, Purchase, Listing, Restaurant, PurchaseStatus
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
            purchases = Purchase.query.filter(Purchase.status == PurchaseStatus.COMPLETED).all()
            if not purchases:
                return False

            data = []
            for purchase in purchases:
                if not purchase.listing or not purchase.listing.restaurant_id:
                    continue
                restaurant = purchase.listing.restaurant
                if restaurant and restaurant.category == self.target_category:
                    data.append({
                        "user_id": purchase.user_id,
                        "listing_id": purchase.listing.id,
                        "quantity": purchase.quantity
                    })

            if not data:
                return False

            df = pd.DataFrame(data)
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
        target_listing = Listing.query.get(listing_id)
        if not target_listing:
            return {"success": False, "message": "Listing not found"}, 404

        restaurant = target_listing.restaurant
        if not restaurant or not restaurant.category:
            return {"success": False, "message": "Restaurant or category not found"}, 500

        service = RecommendationSystemService(target_category=restaurant.category)

        if not service.initialize_model():
            return {"success": False, "message": "Could not initialize recommendation model"}, 500

        try:
            try:
                idx = service.listing_ids.index(listing_id)
            except ValueError:
                return {"success": False, "message": "Listing not in training data"}, 404

            distances, indices = service.model.kneighbors(
                [service.purchase_matrix[idx]],
                n_neighbors=min(service.k_neighbors + 1, len(service.listing_ids))
            )

            similarities = 1 - distances.flatten()

            recommendations = []
            for i, sim in zip(indices.flatten(), similarities):
                rec_id = service.listing_ids[i]
                if rec_id == listing_id:
                    continue

                rec_listing = Listing.query.get(rec_id)
                if rec_listing:
                    rec_restaurant = rec_listing.restaurant
                    recommendations.append({
                        "listing_id": rec_listing.id,
                        "title": rec_listing.title,
                        "restaurant_name": rec_restaurant.restaurantName if rec_restaurant else "Unknown",
                        "similarity_score": float(sim),
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
