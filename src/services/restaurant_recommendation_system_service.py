from datetime import datetime
from sqlalchemy import func, and_
from src.models import db, Purchase, Restaurant, Listing
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
            # Tüm completed satın almaları çek
            purchases = Purchase.query.filter_by(status='COMPLETED').all()
            if not purchases:
                return False

            data = []
            for purchase in purchases:
                listing = purchase.listing
                if listing:
                    data.append({'user_id': purchase.user_id, 'restaurant_id': listing.restaurant_id})

            df = pd.DataFrame(data)
            if df.empty:
                return False

            # Kullanıcı-restaurant matrisi (binary interaction)
            user_restaurant_matrix = df.pivot_table(index='restaurant_id', columns='user_id', aggfunc=lambda x: 1, fill_value=0)

            self.restaurant_matrix = user_restaurant_matrix.values
            self.restaurant_ids = user_restaurant_matrix.index.tolist()

            # KNN modelini oluştur
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
            return {
                "success": False,
                "message": "Could not initialize recommendation model"
            }, 404

        try:
            purchases = Purchase.query.filter_by(user_id=user_id, status='COMPLETED').all()

            if not purchases:
                return {
                    "success": False,
                    "message": "No purchase history found for this user"
                }, 404

            restaurant_ids = set()
            for purchase in purchases:
                listing = purchase.listing
                if listing:
                    restaurant_ids.add(listing.restaurant_id)

            if not restaurant_ids:
                return {
                    "success": False,
                    "message": "No restaurants found in user's purchase history"
                }, 404

            all_recommendations = []
            for restaurant_id in restaurant_ids:
                try:
                    restaurant_idx = service.restaurant_ids.index(restaurant_id)
                except ValueError:
                    continue

                distances, indices = service.model.kneighbors(
                    [service.restaurant_matrix[restaurant_idx]],
                    n_neighbors=min(service.k_neighbors + 1, len(service.restaurant_ids))
                )

                similarities = 1 - distances.flatten()

                for idx, similarity in zip(indices.flatten(), similarities):
                    rec_restaurant_id = service.restaurant_ids[idx]
                    if rec_restaurant_id != restaurant_id:
                        rec_restaurant = Restaurant.query.get(rec_restaurant_id)
                        base_restaurant = Restaurant.query.get(restaurant_id)
                        if rec_restaurant and base_restaurant:
                            # Sadece aynı kategoride olanları al
                            if rec_restaurant.category != base_restaurant.category:
                                continue

                            recommendation = {
                                "restaurant_id": rec_restaurant.id,
                                "restaurant_name": rec_restaurant.restaurantName,
                                "category": rec_restaurant.category,
                                "similarity_score": float(similarity),
                                "address": f"{rec_restaurant.latitude}, {rec_restaurant.longitude}",
                                "based_on": {
                                    "restaurant_id": base_restaurant.id,
                                    "restaurant_name": base_restaurant.restaurantName,
                                    "category": base_restaurant.category
                                }
                            }

                            if not any(r.get('restaurant_id') == rec_restaurant.id for r in all_recommendations):
                                all_recommendations.append(recommendation)

            '''all_recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)

            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "restaurants_from_history": list(restaurant_ids),
                    "recommendations": all_recommendations
                }
            }, 200'''

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
            return {
                "success": False,
                "message": f"Error getting recommendations: {str(e)}"
            }, 500
