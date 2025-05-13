from datetime import datetime
from src.models import Restaurant, Purchase, PurchaseStatus, RestaurantComment
from decimal import Decimal


class RestaurantAnalyticsService:
    @staticmethod
    def get_owner_analytics(owner_id):
        today = datetime.utcnow()
        start_date = datetime(today.year, today.month, 1)

        restaurants = Restaurant.query.filter_by(owner_id=owner_id).all()
        restaurant_ids = [r.id for r in restaurants]

        if not restaurant_ids:
            return {
                "success": False,
                "message": "No restaurants found for this owner"
            }, 404

        monthly_purchases = Purchase.query.filter(
            Purchase.restaurant_id.in_(restaurant_ids),
            Purchase.status == PurchaseStatus.COMPLETED,
            Purchase.purchase_date >= start_date
        ).all()

        monthly_products = sum(p.quantity for p in monthly_purchases)
        monthly_revenue = sum(Decimal(p.total_price) for p in monthly_purchases)

        regions = {}
        for purchase in monthly_purchases:
            if purchase.delivery_district:
                district = purchase.delivery_district
                regions[district] = regions.get(district, 0) + 1

        restaurant_stats = {}
        for restaurant in restaurants:
            comments = RestaurantComment.query.filter_by(restaurant_id=restaurant.id) \
                .order_by(RestaurantComment.timestamp.desc()).all()

            restaurant_stats[restaurant.restaurantName] = {
                "id": restaurant.id,
                "average_rating": float(restaurant.rating) if restaurant.rating else 0,
                "total_ratings": restaurant.ratingCount,
                "recent_comments": [{
                    "user_name": comment.user.name,
                    "rating": float(comment.rating),
                    "comment": comment.comment,
                    "timestamp": comment.timestamp if isinstance(comment.timestamp, str) else comment.timestamp.isoformat()
                } for comment in comments[:5]]
            }

        return {
            "success": True,
            "data": {
                "monthly_stats": {
                    "total_products_sold": monthly_products,
                    "total_revenue": str(monthly_revenue),
                    "period": f"{today.year}-{today.month:02d}"
                },
                "regional_distribution": regions,
                "restaurant_ratings": restaurant_stats
            }
        }, 200

    @staticmethod
    def get_restaurant_analytics(restaurant_id):
        today = datetime.utcnow()
        start_date = datetime(today.year, today.month, 1)

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return {
                "success": False,
                "message": f"Restaurant with ID {restaurant_id} not found"
            }, 404

        monthly_purchases = Purchase.query.filter(
            Purchase.restaurant_id == restaurant_id,
            Purchase.status == PurchaseStatus.COMPLETED,
            Purchase.purchase_date >= start_date
        ).all()

        monthly_products = sum(p.quantity for p in monthly_purchases)
        monthly_revenue = sum(Decimal(p.total_price) for p in monthly_purchases)

        regions = {}
        for purchase in monthly_purchases:
            if purchase.delivery_district:
                district = purchase.delivery_district
                regions[district] = regions.get(district, 0) + 1

        comments = RestaurantComment.query.filter_by(restaurant_id=restaurant_id) \
            .order_by(RestaurantComment.timestamp.desc()).all()

        restaurant_stats = {
            "id": restaurant.id,
            "name": restaurant.restaurantName,
            "average_rating": float(restaurant.rating) if restaurant.rating else 0,
            "total_ratings": restaurant.ratingCount,
            "recent_comments": [{
                "user_name": comment.user.name,
                "rating": float(comment.rating),
                "comment": comment.comment,
                "timestamp": comment.timestamp if isinstance(comment.timestamp, str) else comment.timestamp.isoformat(),
                "badges": [{
                    "name": badge.badge_name,
                    "is_positive": badge.is_positive
                } for badge in comment.badges]
            } for comment in comments[:5]]
        }

        return {
            "success": True,
            "data": {
                "monthly_stats": {
                    "total_products_sold": monthly_products,
                    "total_revenue": str(monthly_revenue),
                    "period": f"{today.year}-{today.month:02d}"
                },
                "regional_distribution": regions,
                "restaurant_stats": restaurant_stats
            }
        }, 200