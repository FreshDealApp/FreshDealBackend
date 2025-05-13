import logging
from datetime import datetime, UTC
from typing import Dict, Any
from src.models import Purchase, Restaurant
from src.services.web_push_notification_service import WebPushNotificationService

logger = logging.getLogger(__name__)

class BusinessNotificationService:

    @staticmethod
    def send_purchase_notification(purchase_id: int) -> bool:
        try:
            purchase = Purchase.query.get(purchase_id)
            if not purchase:
                logger.warning(f"Purchase {purchase_id} not found")
                return False

            restaurant = Restaurant.query.get(purchase.restaurant_id)
            if not restaurant or not restaurant.owner_id:
                logger.warning(f"Restaurant or owner not found for purchase {purchase_id}")
                return False

            notification_data: Dict[str, Any] = {
                'type': 'new_purchase',
                'purchase_id': purchase.id,
                'listing_title': purchase.listing.title if purchase.listing else 'Unknown',
                'total_price': str(purchase.total_price),
                'quantity': purchase.quantity,
                'restaurant_id': restaurant.id,
                'restaurant_name': restaurant.restaurantName
            }

            title = "New Order Received!"
            body = f"New order: {purchase.quantity}x {notification_data['listing_title']} at {restaurant.restaurantName}"

            # Send web notification only (restaurant owners don't use mobile)
            web_success = WebPushNotificationService.send_notification_to_user_web(
                restaurant.owner_id,
                title,
                body,
                notification_data,
                icon="/static/images/logo.png",
                tag=f"purchase_{purchase.id}",
                require_interaction=True
            )

            return web_success

        except Exception as e:
            logger.error(f"Error sending business notification for purchase {purchase_id}: {str(e)}")
            return False