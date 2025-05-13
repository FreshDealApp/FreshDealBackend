# services/user_services.py

import logging
import coloredlogs
from sqlalchemy import func, desc
from werkzeug.security import check_password_hash, generate_password_hash
from src.models import db, User, CustomerAddress, UserFavorites, Purchase, Restaurant, PurchaseStatus

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set to INFO since all logs are at this level

# Define log format
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Install coloredlogs with the defined format
coloredlogs.install(level='INFO', logger=logger, fmt=log_format)

def fetch_user_data(user_id):
    """
    Fetch user information and their associated addresses.
    """
    logger.info(f"Fetching data for user_id: {user_id}")
    user = User.query.filter_by(id=user_id).first()
    if not user:
        logger.info(f"User with id {user_id} not found.")
        return None, "User not found"

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "email_verified": user.email_verified
    }

    user_addresses = CustomerAddress.query.filter_by(user_id=user_id).all()
    user_address_list = [
        {
            "id": addr.id,
            "title": addr.title,
            "longitude": float(addr.longitude),
            "latitude": float(addr.latitude),
            "street": addr.street,
            "neighborhood": addr.neighborhood,
            "district": addr.district,
            "province": addr.province,
            "country": addr.country,
            "postalCode": addr.postalCode,
            "apartmentNo": addr.apartmentNo,
            "doorNo": addr.doorNo,
            "is_primary": addr.is_primary,
        }
        for addr in user_addresses
    ]

    logger.info(f"User data: {user_data}")
    logger.info(f"User addresses: {user_address_list}")

    return {
        "user_data": user_data,
        "user_address_list": user_address_list
    }, None

def change_password(user_id, old_password, new_password):
    """
    Update the user's password if the old password matches.
    """
    logger.info(f"Attempting to change password for user_id: {user_id}")
    user = User.query.filter_by(id=user_id).first()
    if not user:
        logger.info(f"User with id {user_id} not found.")
        return False, "User not found"

    if not check_password_hash(user.password, old_password):
        logger.info(f"Incorrect old password for user_id: {user_id}")
        return False, "Old password is incorrect"

    user.password = generate_password_hash(new_password)
    db.session.commit()
    logger.info(f"Password updated successfully for user_id: {user_id}")
    return True, "Password updated successfully"

def change_username(user_id, new_username):
    """
    Update the user's username.
    """
    logger.info(f"Attempting to change username for user_id: {user_id} to '{new_username}'")
    user = User.query.filter_by(id=user_id).first()
    if not user:
        logger.info(f"User with id {user_id} not found.")
        return False, "User not found"

    old_username = user.name
    user.name = new_username
    db.session.commit()
    logger.info(f"Username changed from '{old_username}' to '{new_username}' for user_id: {user_id}")
    return True, "Username updated successfully"

def change_email(user_id, old_email, new_email):
    """
    Update the user's email and send a mock verification email.
    """
    logger.info(f"Attempting to change email for user_id: {user_id} from '{old_email}' to '{new_email}'")
    user = User.query.filter_by(id=user_id).first()
    if not user:
        logger.info(f"User with id {user_id} not found.")
        return False, "User not found"

    if user.email != old_email:
        logger.info(f"Old email '{old_email}' does not match the current email for user_id: {user_id}")
        return False, "Old email is incorrect"

    user.email = new_email
    db.session.commit()
    send_verification_email(new_email)
    logger.info(f"Email updated to '{new_email}' for user_id: {user_id}")
    return True, "Email updated successfully"

def send_verification_email(email):
    """
    Mock function to simulate sending a verification email.
    """
    # In a real application, integrate with an email service provider here
    logger.info(f"Verification email sent to {email}")

def add_favorite(user_id, restaurant_id):
    """
    Add a restaurant to the user's favorites.
    """
    logger.info(f"User_id: {user_id} is attempting to add restaurant_id: {restaurant_id} to favorites")
    existing_favorite = UserFavorites.query.filter_by(user_id=user_id, restaurant_id=restaurant_id).first()
    if existing_favorite:
        logger.info(f"Restaurant_id: {restaurant_id} is already in favorites for user_id: {user_id}")
        return False, "Restaurant is already in your favorites"

    favorite = UserFavorites(user_id=user_id, restaurant_id=restaurant_id)
    db.session.add(favorite)
    db.session.commit()
    logger.info(f"Restaurant_id: {restaurant_id} added to favorites for user_id: {user_id}")
    return True, "Restaurant added to favorites"

def remove_favorite(user_id, restaurant_id):
    """
    Remove a restaurant from the user's favorites.
    """
    logger.info(f"User_id: {user_id} is attempting to remove restaurant_id: {restaurant_id} from favorites")
    favorite = UserFavorites.query.filter_by(user_id=user_id, restaurant_id=restaurant_id).first()
    if not favorite:
        logger.info(f"Favorite with restaurant_id: {restaurant_id} not found for user_id: {user_id}")
        return False, "Favorite not found"

    db.session.delete(favorite)
    db.session.commit()
    logger.info(f"Restaurant_id: {restaurant_id} removed from favorites for user_id: {user_id}")
    return True, "Restaurant removed from favorites"


def get_favorites(user_id):
    """
    Get a list of the user's favorite restaurants.
    """
    logger.info(f"Fetching favorites for user_id: {user_id}")
    favorites = UserFavorites.query.filter_by(user_id=user_id).all()
    if not favorites:
        logger.info(f"No favorites found for user_id: {user_id}")
        return []

    # Corrected line
    favorite_restaurants = [favorite.restaurant_id for favorite in favorites]

    logger.info(f"Favorites for user_id {user_id}: {favorite_restaurants}")
    return favorite_restaurants


def authenticate_user(email=None, phone_number=None, password=None):
    """
    Authenticate a user by email or phone number and password.
    """
    logger.info(f"Login attempt with email: '{email}' and phone_number: '{phone_number}'")
    if email:
        user = User.query.filter_by(email=email).first()
    elif phone_number:
        user = User.query.filter_by(phone_number=phone_number).first()
    else:
        logger.info("No email or phone number provided for authentication.")
        return False, "Email or phone number is required.", None

    if not user:
        logger.info(f"Authentication failed: User not found with email '{email}' or phone_number '{phone_number}'")
        return False, "User does not exist.", None

    if not check_password_hash(user.password, password):
        logger.info(f"Authentication failed: Incorrect password for user_id {user.id}")
        return False, "Incorrect password.", None

    logger.info(f"User_id {user.id} authenticated successfully.")
    return True, "Authenticated successfully.", user


def get_user_recent_restaurants_service(user_id):
    """
    Get a list of recently ordered restaurants for a user (up to 20 unique restaurants)
    """
    try:
        # Query to get the latest purchase date for each restaurant
        recent_restaurants = db.session.query(
            Purchase.restaurant_id,
            func.max(Purchase.purchase_date).label('last_order_date')
        ).filter(
            Purchase.user_id == user_id,
            Purchase.status.in_([PurchaseStatus.COMPLETED, PurchaseStatus.ACCEPTED])
        ).group_by(
            Purchase.restaurant_id
        ).order_by(
            desc('last_order_date')
        ).limit(20).all()

        restaurant_ids = [restaurant.restaurant_id for restaurant in recent_restaurants]

        return {
            "success": True,
            "restaurants": restaurant_ids
        }, 200

    except Exception as e:
        return {
            "success": False,
            "message": "An error occurred while fetching recent restaurants",
            "error": str(e)
        }, 500