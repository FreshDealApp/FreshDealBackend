import os
from . import db
from sqlalchemy import Integer, String, DECIMAL, Boolean, Float
from sqlalchemy.orm import validates, relationship
from datetime import datetime, UTC
from .restaurant_punishment_model import RestaurantPunishment


class Restaurant(db.Model):
    __tablename__ = 'restaurants'

    id = db.Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    owner_id = db.Column(Integer, db.ForeignKey('users.id'), nullable=False)

    restaurantName = db.Column(String(80), nullable=False)
    restaurantDescription = db.Column(String(500), nullable=True)
    restaurantEmail = db.Column(String(80), nullable=True)
    restaurantPhone = db.Column(String(20), nullable=True)
    longitude = db.Column(DECIMAL(9, 6), nullable=False)
    latitude = db.Column(DECIMAL(9, 6), nullable=False)
    category = db.Column(String(80), nullable=False)

    workingDays = db.Column(String(500), nullable=True)
    workingHoursStart = db.Column(String(5), nullable=True)
    workingHoursEnd = db.Column(String(5), nullable=True)

    listings = db.Column(Integer, nullable=False, default=0)
    rating = db.Column(DECIMAL(3, 2), nullable=True)
    ratingCount = db.Column(Integer, nullable=False, default=0)

    image_url = db.Column(String(2083), nullable=True)

    pickup = db.Column(Boolean, nullable=False, default=False)
    delivery = db.Column(Boolean, nullable=False, default=False)

    maxDeliveryDistance = db.Column(Float, nullable=True)
    deliveryFee = db.Column(DECIMAL(10, 2), nullable=True)
    minOrderAmount = db.Column(DECIMAL(10, 2), nullable=True)

    flash_deals_available = db.Column(Boolean, nullable=False, default=False)
    flash_deals_count = db.Column(Integer, nullable=False, default=0)

    comments = relationship("RestaurantComment", back_populates="restaurant", cascade="all, delete-orphan")
    purchases = relationship('Purchase', back_populates='restaurant')
    punishments = relationship('RestaurantPunishment', backref='restaurant', lazy=True)

    @validates('workingDays')
    def validate_working_days(self, key, working_days):
        valid_days = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}
        days_list = working_days.split(',')

        if not all(day in valid_days for day in days_list):
            raise ValueError(f"Working days must be one of {', '.join(valid_days)}")

        return working_days

    @validates('workingHoursStart', 'workingHoursEnd')
    def validate_working_hours(self, key, value):
        try:
            hours, minutes = map(int, value.split(':'))
            if not (0 <= hours < 24) or not (0 <= minutes < 60):
                raise ValueError("Time must be in HH:MM format with valid hour (00-23) and minute (00-59).")
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM (24-hour format).")

        return value

    @validates('rating')
    def validate_rating(self, key, rating):
        if rating is not None and not (0 <= rating <= 5):
            raise ValueError("Rating must be between 0.00 and 5.00.")
        return rating

    def update_rating(self, new_rating):
        from decimal import Decimal
        new_rating = Decimal(str(new_rating))
        if self.rating is None:
            self.rating = new_rating
            self.ratingCount = 1
        else:
            total_rating = self.rating * self.ratingCount
            self.ratingCount += 1
            self.rating = (total_rating + new_rating) / self.ratingCount

    def update_listings_count(self, increment=True):
        if increment:
            self.listings += 1
        else:
            self.listings = max(0, self.listings - 1)
        db.session.add(self)

    def try_delete_image_file(self, image_url):
        from ..routes.restaurant_routes import UPLOAD_FOLDER

        if not image_url:
            return True, "No image to delete"

        try:
            filename = image_url.split('/')[-1]
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, f"Successfully deleted image: {filename}"
            return True, f"Image file not found: {filename}"
        except Exception as e:
            return False, f"Failed to delete image file: {str(e)}"

    def is_active(self):
        current_time = datetime.now(UTC)
        punishment = RestaurantPunishment.query.filter(
            RestaurantPunishment.restaurant_id == self.id,
            (
                    (RestaurantPunishment.punishment_type == 'PERMANENT') |
                    (
                            (RestaurantPunishment.punishment_type == 'TEMPORARY') &
                            (RestaurantPunishment.end_date > current_time)
                    )
            )
        ).first()
        return punishment is None

    def can_accept_orders(self):
        return self.is_active()

    def can_update_details(self):
        return self.is_active()

    def increment_flash_deals_count(self):
        self.flash_deals_count += 1
        if self.flash_deals_count >= 3:
            self.flash_deals_available = False
        db.session.add(self)
        db.session.commit()

    @classmethod
    def delete_restaurant_service(cls, restaurant_id, owner_id):
        from .listing_model import Listing

        restaurant = cls.query.get(restaurant_id)
        if not restaurant:
            return {"success": False, "message": f"Restaurant with ID {restaurant_id} not found."}, 404

        if str(owner_id) != str(restaurant.owner_id):
            return {"success": False, "message": "You are not the owner of this restaurant."}, 403

        deletion_log = []
        image_url = restaurant.image_url

        try:
            listings = Listing.query.filter_by(restaurant_id=restaurant_id).all()

            for listing in listings:
                print(f"[{datetime.now(UTC)}] Attempting to delete listing {listing.id}")
                success, message = Listing.delete_listing(listing.id)
                deletion_log.append({
                    "listing_id": listing.id,
                    "success": success,
                    "message": message,
                    "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                })

                if not success:
                    print(f"[{datetime.now(UTC)}] Warning: Issue with listing {listing.id}: {message}")

            db.session.delete(restaurant)
            db.session.commit()

            image_delete_success, image_delete_message = restaurant.try_delete_image_file(image_url)

            response = {
                "success": True,
                "message": f"Restaurant with ID {restaurant_id} deleted successfully",
                "details": {
                    "restaurant_id": restaurant_id,
                    "listings_processed": len(listings),
                    "deletion_log": deletion_log,
                    "image_deletion": {
                        "success": image_delete_success,
                        "message": image_delete_message
                    },
                    "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                }
            }

            print(f"[{datetime.now(UTC)}] Successfully deleted restaurant {restaurant_id} "
                  f"and {len(listings)} listings")

            return response, 200

        except Exception as e:
            db.session.rollback()
            error_message = f"Error during restaurant deletion: {str(e)}"
            print(f"[{datetime.now(UTC)}] {error_message}")
            return {
                "success": False,
                "message": error_message,
                "details": {
                    "restaurant_id": restaurant_id,
                    "error": str(e),
                    "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                }
            }, 500