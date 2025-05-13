from datetime import datetime
from sqlalchemy import func, and_
from src.models import db, Purchase, Restaurant, Listing, PurchaseStatus
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
            purchases = Purchase.query.filter(Purchase.status == PurchaseStatus.COMPLETED).all()
            if not purchases:
                return False

            data = []
            for purchase in purchases:
                if purchase.listing and purchase.listing.restaurant_id:
                    data.append({
                        'user_id': purchase.user_id,
                        'restaurant_id': purchase.listing.restaurant_id
                    })

            df = pd.DataFrame(data)
            if df.empty:
                return False

            user_restaurant_matrix = df.pivot_table(
                index='restaurant_id',
                columns='user_id',
                aggfunc=lambda x: 1,
                fill_value=0
            )

            self.restaurant_matrix = user_restaurant_matrix.values
            self.restaurant_ids = user_restaurant_matrix.index.tolist()

            self.model = NearestNeighbors(
                n_neighbors=min(self.k_neighbors + 1, len(self.restaurant_ids)),
                metric='cosine',
                algorithm='brute'
            )
            self.model.fit(self.restaurant_matrix)
            self.is_initialized = True
            return True

        except Exception as e:
            print(f"Error initializing model: {e}")
            return False

    @staticmethod
    def get_recommendations_by_user(user_id):
        service = RestaurantRecommendationSystemService()
        if not service.initialize_model():
            return {"success": False, "message": "Could not initialize recommendation model"}, 404

        try:
            purchases = Purchase.query.filter(
                Purchase.user_id == user_id,
                Purchase.status == PurchaseStatus.COMPLETED
            ).all()

            if not purchases:
                return {"success": False, "message": "No purchase history found for this user"}, 404

            restaurant_ids = set()
            for purchase in purchases:
                if purchase.listing and purchase.listing.restaurant_id:
                    restaurant_ids.add(purchase.listing.restaurant_id)

            if not restaurant_ids:
                return {"success": False, "message": "No restaurants found in user's purchase history"}, 404

            all_recommendations = []
            for restaurant_id in restaurant_ids:
                try:
                    idx = service.restaurant_ids.index(restaurant_id)
                except ValueError:
                    continue

                distances, indices = service.model.kneighbors(
                    [service.restaurant_matrix[idx]],
                    n_neighbors=min(service.k_neighbors + 1, len(service.restaurant_ids))
                )

                similarities = 1 - distances.flatten()

                for i, sim in zip(indices.flatten(), similarities):
                    rec_id = service.restaurant_ids[i]
                    if rec_id == restaurant_id:
                        continue

                    rec_rest = Restaurant.query.get(rec_id)
                    base_rest = Restaurant.query.get(restaurant_id)

                    if rec_rest and base_rest and rec_rest.category == base_rest.category:
                        if not any(r['restaurant_id'] == rec_id for r in all_recommendations):
                            all_recommendations.append({
                                "restaurant_id": rec_rest.id,
                                "restaurant_name": rec_rest.restaurantName,
                                "category": rec_rest.category,
                                "similarity_score": float(sim),
                                "address": f"{rec_rest.latitude}, {rec_rest.longitude}",
                                "based_on": {
                                    "restaurant_id": base_rest.id,
                                    "restaurant_name": base_rest.restaurantName,
                                    "category": base_rest.category
                                }
                            })

            all_recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
            top_recommendations = all_recommendations[:10]

            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "restaurants_from_history": list(restaurant_ids),
                    "recommendations": top_recommendations
                }
            }, 200

        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}, 500
