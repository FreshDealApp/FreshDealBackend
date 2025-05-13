import os
import uuid

from sqlalchemy import and_
from werkzeug.utils import secure_filename
from decimal import Decimal

from src.models import db, UserCart, Purchase, Restaurant, CustomerAddress

from src.models.purchase_model import PurchaseStatus
from src.services.notification_service import NotificationService
from src.services.achievement_service import AchievementService
from src.services.business_notification_service import BusinessNotificationService
from src.services.discount_service import apply_discount


def create_purchase_order_service(user_id, data=None):
    try:
        cart_items = UserCart.query.filter_by(user_id=user_id).all()

        if not cart_items:
            return {"message": "Cart is empty"}, 400

        purchases = []
        cart_items_to_clear = []

        is_delivery = data.get('is_delivery', False) if data else False
        notes = data.get('pickup_notes') if not is_delivery else data.get('delivery_notes')
        is_flash_deal = data.get('flashdealsactivated', 0) == 1 if data else False

        # Get user's primary address or the specified address
        address_id = data.get('address_id')
        if address_id:
            address = CustomerAddress.query.filter_by(id=address_id, user_id=user_id).first()
        else:
            address = CustomerAddress.query.filter_by(user_id=user_id, is_primary=True).first()

        if not address:
            return {"message": "No valid address found for the user"}, 400

        for item in cart_items:
            listing = item.listing
            if not listing:
                return {"message": f"Listing (ID: {item.listing_id}) not found"}, 404

            if item.count > listing.count:
                return {
                    "message": f"Cannot purchase {item.count} of {listing.title}. Only {listing.count} left in stock."
                }, 400

            price_to_use = listing.delivery_price if is_delivery else listing.pick_up_price
            if price_to_use is None:
                price_to_use = listing.original_price

            restaurant = Restaurant.query.get(listing.restaurant_id)
            if not restaurant:
                return {"message": f"Restaurant (ID: {listing.restaurant_id}) not found"}, 404

            # Check if flash deal is activated and available
            if is_flash_deal and not restaurant.flash_deals_available:
                return {"message": f"Flash deals are not available for restaurant: {restaurant.restaurantName}"}, 400

            delivery_fee = restaurant.deliveryFee if is_delivery else 0
            total_price = (price_to_use * item.count) + delivery_fee

            # Create address string from components
            address_str = f"{address.street}"
            if address.apartmentNo:
                address_str += f" No:{address.apartmentNo}"
            if address.doorNo:
                address_str += f" Door:{address.doorNo}"
            if address.neighborhood:
                address_str += f", {address.neighborhood}"

            try:
                purchase = Purchase(
                    user_id=user_id,
                    listing_id=listing.id,
                    quantity=item.count,
                    restaurant_id=listing.restaurant_id,
                    total_price=total_price,
                    status=PurchaseStatus.PENDING,
                    is_delivery=is_delivery,
                    is_flash_deal=is_flash_deal,
                    address_title=address.title,
                    delivery_address=address_str,
                    delivery_district=address.district,
                    delivery_province=address.province,
                    delivery_country=address.country,
                    delivery_notes=notes
                )
            except ValueError as e:
                db.session.rollback()
                return {"message": str(e)}, 400

            if not listing.decrease_stock(item.count):
                db.session.rollback()
                return {
                    "message": f"Cannot create purchase. Not enough stock available for {listing.title}. Current stock: {listing.count}"
                }, 400

            db.session.add(purchase)
            purchases.append(purchase)
            cart_items_to_clear.append(item)

        # Apply discount based on total purchase amount
        total_before_discount, discount_amount, purchases_with_discount = apply_discount(purchases)

        for item in cart_items_to_clear:
            db.session.delete(item)

        # Increment flash deals count if applicable
        processed_restaurants = set()
        for purchase in purchases_with_discount:
            if purchase.is_flash_deal and purchase.restaurant_id not in processed_restaurants:
                restaurant = Restaurant.query.get(purchase.restaurant_id)
                if restaurant:
                    restaurant.increment_flash_deals_count()
                    processed_restaurants.add(purchase.restaurant_id)

        db.session.commit()

        # Send notifications to restaurant owners for each purchase
        for purchase in purchases_with_discount:
            BusinessNotificationService.send_purchase_notification(purchase.id)

        # Prepare response with discount information
        response = {
            "message": "Purchase order created successfully, waiting for restaurant approval",
            "purchases": [p.to_dict() for p in purchases_with_discount]
        }

        # Include discount information if a discount was applied
        if discount_amount > Decimal('0'):
            response["discount_info"] = {
                "total_before_discount": str(total_before_discount),
                "discount_amount": str(discount_amount),
                "total_after_discount": str(total_before_discount - discount_amount)
            }

        return response, 201

    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred", "error": str(e)}, 500


def handle_restaurant_response_service(purchase_id, owner_id, action):
    """
    Second step: Restaurant accepts or rejects the order.
    The JWT token provides the owner's id rather than the restaurant id.
    """
    try:
        purchase = Purchase.query.get(purchase_id)
        if not purchase:
            print(f"[DEBUG] Purchase with id {purchase_id} not found.")
            return {"message": "Purchase not found"}, 404

        # Debug prints for owner check
        print(f"[DEBUG] Received owner_id (from token): {owner_id} (type: {type(owner_id)})")

        # Retrieve the restaurant using the listing's restaurant_id
        restaurant = Restaurant.query.get(purchase.listing.restaurant_id)
        if not restaurant:
            print(f"[DEBUG] Restaurant with id {purchase.listing.restaurant_id} not found.")
            return {"message": "Associated restaurant not found"}, 404

        print(f"[DEBUG] Restaurant's owner_id: {restaurant.owner_id} (type: {type(restaurant.owner_id)})")

        if int(owner_id) != int(restaurant.owner_id):
            print("[DEBUG] Unauthorized: The owner_id from token does not match the restaurant owner_id.")
            return {"message": "Unauthorized"}, 403

        if action not in ['accept', 'reject']:
            print(f"[DEBUG] Invalid action provided: {action}")
            return {"message": "Invalid action"}, 400

        try:
            new_status = PurchaseStatus.ACCEPTED if action == 'accept' else PurchaseStatus.REJECTED
            print(f"[DEBUG] Updating purchase status to: {new_status}")
            purchase.update_status(new_status)

            if action == 'reject':
                # Restore stock when rejected
                print(f"[DEBUG] Restoring stock. Before: {purchase.listing.count}, Adding back: {purchase.quantity}")
                purchase.listing.count += purchase.quantity

            db.session.commit()
            print(f"[DEBUG] Purchase {action}ed successfully.")

            # Send notification to user based on action
            try:
                user_id = purchase.user_id
                listing = purchase.listing
                restaurant_name = restaurant.restaurantName

                if action == 'accept':
                    NotificationService.send_notification_to_user(
                        user_id=user_id,
                        title="Order Accepted",
                        body=f"Your order for {listing.title} from {restaurant_name} has been accepted!",
                        data={
                            "type": "order_status",
                            "purchase_id": purchase.id,
                            "status": "accepted"
                        }
                    )
                else:  # action == 'reject'
                    NotificationService.send_notification_to_user(
                        user_id=user_id,
                        title="Order Rejected",
                        body=f"Unfortunately, your order for {listing.title} from {restaurant_name} has been rejected.",
                        data={
                            "type": "order_status",
                            "purchase_id": purchase.id,
                            "status": "rejected"
                        }
                    )
                print(f"[DEBUG] Notification sent to user {user_id} for {action} action.")
            except Exception as e:
                # Log the error but don't disrupt the main flow
                print(f"[DEBUG] Failed to send notification: {str(e)}")

            return {
                "message": f"Purchase {action}ed successfully",
                "purchase": purchase.to_dict(include_relations=True)
            }, 200

        except ValueError as e:
            db.session.rollback()
            print(f"[DEBUG] ValueError during status update: {e}")
            return {"message": str(e)}, 400

    except Exception as e:
        db.session.rollback()
        print(f"[DEBUG] General Exception: {e}")
        return {"message": "An error occurred", "error": str(e)}, 500


# In your purchase_service.py

def get_restaurant_purchases_service(restaurant_id):
    """
    Get all purchases for a restaurant
    """
    try:
        purchases = Purchase.get_restaurant_purchases(restaurant_id)
        return {
            "purchases": [purchase.to_dict() for purchase in purchases]
        }, 200
    except Exception as e:
        return {"message": "An error occurred", "error": str(e)}, 500


def get_user_active_orders_service(user_id):
    """
    Get all active orders for a user (PENDING, ACCEPTED)
    """
    try:
        # Use the class method from the updated Purchase model
        active_orders = Purchase.get_active_purchases_for_user(user_id)

        return {
            "active_orders": [
                {
                    "purchase_id": order.id,
                    "restaurant_name": order.restaurant.restaurantName,
                    "listing_title": order.listing.title,
                    "quantity": order.quantity,
                    "total_price": order.formatted_total_price,  # Using new formatted_total_price property
                    "status": order.status.value,
                    "purchase_date": order.purchase_date.isoformat(),
                    "is_active": order.is_active,  # Added new property
                    "is_delivery": order.is_delivery,
                    "delivery_address": order.delivery_address if order.is_delivery else None,
                    "delivery_notes": order.delivery_notes if order.is_delivery else None,
                    "restaurant_details": {
                        "id": order.restaurant.id,
                        "name": order.restaurant.restaurantName,
                        "image_url": order.restaurant.image_url
                    }
                }
                for order in active_orders
            ]
        }, 200
    except Exception as e:
        return {"message": "An error occurred", "error": str(e)}, 500


def get_user_previous_orders_service(user_id, page=1, per_page=10):
    """
    Get completed or rejected orders for a user with pagination
    """
    try:
        # Calculate offset
        offset = (page - 1) * per_page

        # Query for completed and rejected orders
        previous_orders = Purchase.query.filter(
            and_(
                Purchase.user_id == user_id,
                Purchase.status.in_([PurchaseStatus.COMPLETED, PurchaseStatus.REJECTED])
            )
        ).order_by(Purchase.purchase_date.desc()) \
            .offset(offset) \
            .limit(per_page) \
            .all()

        # Get total count for pagination
        total_orders = Purchase.query.filter(
            and_(
                Purchase.user_id == user_id,
                Purchase.status.in_([PurchaseStatus.COMPLETED, PurchaseStatus.REJECTED])
            )
        ).count()

        # Calculate pagination metadata
        total_pages = (total_orders + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "orders": [
                order.to_dict(include_relations=True)  # Using enhanced to_dict method
                for order in previous_orders
            ],
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "per_page": per_page,
                "total_orders": total_orders,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }, 200
    except Exception as e:
        return {"message": "An error occurred", "error": str(e)}, 500


# Add these helper methods to make the code more maintainable
def get_paginated_orders_query(user_id, status_list):
    """
    Helper method to create a base query for orders with specific statuses
    """
    return Purchase.query.filter(
        and_(
            Purchase.user_id == user_id,
            Purchase.status.in_(status_list)
        )
    ).order_by(Purchase.purchase_date.desc())


# You might also want to add this new service for getting order details
def get_order_details_service(user_id, purchase_id):
    """
    Get detailed information about a specific order
    """
    try:
        order = Purchase.query.filter_by(id=purchase_id, user_id=user_id).first()

        if not order:
            return {"message": "Order not found"}, 404

        return {
            "order": order.to_dict(include_relations=True)
        }, 200
    except Exception as e:
        return {"message": "An error occurred", "error": str(e)}, 500


# Define the absolute path for the upload folder (adjust as needed)
# You might share this with your listings_service or define it in a common config file.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'routes', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webm'}

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Return True if the filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_completion_image_service(purchase_id, owner_id, file_obj, url_for_func):
    """
    Process the uploaded completion image file for a purchase.

    - Validates that the file is provided and has an allowed extension.
    - Saves the file with a unique filename in the upload folder.
    - Constructs the image URL using url_for_func.
    - Validates that the purchase exists and the current owner (from token)
      owns the associated restaurant.
    - Updates the purchase's completion image URL and status to COMPLETED.
    """
    try:
        # Retrieve the purchase record
        purchase = Purchase.query.get(purchase_id)
        if not purchase:
            print(f"[DEBUG] Purchase with id {purchase_id} not found.")
            return {"message": "Purchase not found"}, 404

        # Retrieve the associated restaurant using the listing's restaurant_id
        restaurant = Restaurant.query.get(purchase.listing.restaurant_id)
        if not restaurant:
            print(f"[DEBUG] Restaurant with id {purchase.listing.restaurant_id} not found.")
            return {"message": "Associated restaurant not found"}, 404

        # Debug: print owner IDs for verification
        print(f"[DEBUG] Received owner_id (from token): {owner_id} (type: {type(owner_id)})")
        print(f"[DEBUG] Restaurant's owner_id: {restaurant.owner_id} (type: {type(restaurant.owner_id)})")
        if int(owner_id) != int(restaurant.owner_id):
            print("[DEBUG] Unauthorized: The owner_id from token does not match the restaurant owner_id.")
            return {"message": "Unauthorized"}, 403

        # Handle the file upload
        if not file_obj:
            print("[DEBUG] No file object provided.")
            return {"message": "No file provided"}, 400

        if not allowed_file(file_obj.filename):
            print(f"[DEBUG] File {file_obj.filename} has an invalid extension.")
            return {"message": "Invalid file type"}, 400

        # Secure the filename and create a unique filename
        original_filename = secure_filename(file_obj.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

        # Save the file to the upload folder
        try:
            file_obj.save(filepath)
            print(f"[DEBUG] File saved to {filepath}")
        except Exception as e:
            print(f"[DEBUG] Error saving file: {e}")
            return {"message": "Error saving file", "error": str(e)}, 500

        # Construct the image URL using the provided url_for_func
        image_url = url_for_func('api_v1.listings.get_uploaded_file', filename=unique_filename, _external=True)
        print(f"[DEBUG] Constructed image URL: {image_url}")

        try:
            # Update purchase's completion image URL and status
            purchase.completion_image_url = image_url
            print("[DEBUG] Setting completion image URL on purchase.")
            purchase.update_status(PurchaseStatus.COMPLETED)
            print("[DEBUG] Updating purchase status to COMPLETED.")

            db.session.commit()
            print("[DEBUG] Completion image added and purchase updated successfully.")

            # Check and award achievements
            try:
                newly_earned_achievements = AchievementService.check_and_award_achievements(purchase.user_id,
                                                                                            purchase.id)

                # If achievements were earned, prepare notification data
                if newly_earned_achievements:

                    # Send notification to user for earned achievements
                    try:
                        for achievement in newly_earned_achievements:
                            NotificationService.send_notification_to_user(
                                user_id=purchase.user_id,
                                title=f"Achievement Unlocked: {achievement.name}",
                                body=f"Congratulations! You've earned the {achievement.name} achievement: {achievement.description}",
                                data={
                                    "type": "achievement",
                                    "achievement_id": achievement.id
                                }
                            )
                    except Exception as notify_error:
                        print(f"[DEBUG] Failed to send achievement notification: {str(notify_error)}")
            except Exception as ach_error:
                print(f"[DEBUG] Error checking achievements: {str(ach_error)}")
            # Send notification about order completion
            try:
                user_id = purchase.user_id
                listing = purchase.listing
                restaurant_name = restaurant.restaurantName

                NotificationService.send_notification_to_user(
                    user_id=user_id,
                    title="Order Ready for Pickup",
                    body=f"Your order for {listing.title} from {restaurant_name} is ready! Restaurant has uploaded a confirmation image.",
                    data={
                        "type": "order_completed",
                        "purchase_id": purchase.id,
                        "image_url": image_url
                    }
                )
                print(f"[DEBUG] Completion notification sent to user {user_id}")
            except Exception as e:
                # Log the error but don't disrupt the main flow
                print(f"[DEBUG] Failed to send completion notification: {str(e)}")

            return {
                "message": "Completion image added successfully",
                "purchase": purchase.to_dict(include_relations=True)
            }, 200

        except ValueError as e:
            db.session.rollback()
            print(f"[DEBUG] ValueError during purchase update: {e}")
            return {"message": str(e)}, 400

    except Exception as e:
        db.session.rollback()
        print(f"[DEBUG] General Exception: {e}")
        return {"message": "An error occurred", "error": str(e)}, 500