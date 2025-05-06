from src.models import db, Purchase, User, CustomerAddress
from datetime import datetime


class ChatbotService:

    @staticmethod
    def start_conversation(user_id):
        # This could be an initial message when starting a conversation with the chatbot
        return {
            "success": True,
            "message": "Hello! How can I assist you today?",
            "options": [
                "🛒 I want to check my order status",
                "❌ I want to cancel my order",
                "🏠 I want to change my address"
            ]
        }

    @staticmethod
    def get_order_status(user_id):
        # Retrieve the most recent active order for the user
        purchase = Purchase.query.filter_by(user_id=user_id).filter(
            Purchase.status != 'CANCELED'
        ).order_by(Purchase.created_at.desc()).first()

        if purchase:
            return {
                "success": True,
                "order_status": purchase.status,
                "listing_id": purchase.listing_id,
                "created_at": purchase.created_at.isoformat()
            }
        else:
            return {"success": False, "message": "No active orders found."}

    @staticmethod
    def cancel_order(user_id):
        # Retrieve the most recent active order for cancellation
        purchase = Purchase.query.filter_by(user_id=user_id).filter(
            Purchase.status != 'CANCELED'
        ).order_by(Purchase.created_at.desc()).first()

        if not purchase:
            return {"success": False, "message": "No active order to cancel."}

        # Cancel the order
        purchase.status = 'CANCELED'
        purchase.canceled_at = datetime.utcnow()
        db.session.commit()

        return {"success": True, "message": "Your order has been successfully canceled."}

    @staticmethod
    def update_user_address(user_id, address_data):
        # Retrieve the user to update their address
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "message": "User not found."}

        # Create or update the address
        new_address = CustomerAddress(
            user_id=user_id,
            title=address_data.get("title", "Primary Address"),
            longitude=address_data["longitude"],
            latitude=address_data["latitude"],
            street=address_data.get("street"),
            neighborhood=address_data.get("neighborhood"),
            district=address_data.get("district"),
            province=address_data.get("province"),
            country=address_data.get("country"),
            postalCode=address_data.get("postalCode"),
            apartmentNo=address_data.get("apartmentNo"),
            doorNo=address_data.get("doorNo"),
            is_primary=address_data.get("is_primary", False)
        )

        db.session.add(new_address)
        db.session.commit()

        return {"success": True, "message": "Your address has been successfully updated."}
