from sqlalchemy.orm import relationship
from . import db, Restaurant
from sqlalchemy import Integer, String, ForeignKey, DECIMAL, DateTime, Float
from datetime import datetime, timedelta, UTC


class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = db.Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    title = db.Column(String(255), nullable=False)
    description = db.Column(String(1000), nullable=True)
    image_url = db.Column(String(2083), nullable=True)
    count = db.Column(Integer, nullable=False, default=1)
    original_price = db.Column(DECIMAL(10, 2), nullable=False)
    pick_up_price = db.Column(DECIMAL(10, 2), nullable=True)
    delivery_price = db.Column(DECIMAL(10, 2), nullable=True)
    consume_within = db.Column(Integer, nullable=False)
    consume_within_type = db.Column(String(5), nullable=False, default='HOURS')
    expires_at = db.Column(DateTime, nullable=False)
    created_at = db.Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    update_count = db.Column(Integer, nullable=False, default=0)
    fresh_score = db.Column(Float, nullable=False, default=100.0)
    available_for_pickup = db.Column(db.Boolean, nullable=True)
    available_for_delivery = db.Column(db.Boolean, nullable=True)
    purchases = relationship('Purchase', back_populates='listing')

    @staticmethod
    def sync_availability(listing, restaurant):
        listing.available_for_pickup = restaurant.pickup
        listing.available_for_delivery = restaurant.delivery

    @classmethod
    def create(cls, **kwargs):
        if kwargs.get('consume_within', 0) < 6:
            raise ValueError("Minimum consume within time is 6 hours")
        restaurant = db.session.query(Restaurant).get(kwargs['restaurant_id'])
        if not restaurant:
            raise ValueError("Invalid restaurant ID.")
        expires_at = datetime.now(UTC) + timedelta(hours=kwargs['consume_within'])
        kwargs['expires_at'] = expires_at
        kwargs['fresh_score'] = 100.0
        kwargs['update_count'] = 0
        listing = cls(**kwargs)
        cls.sync_availability(listing, restaurant)
        return listing

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "count": self.count,
            "original_price": float(self.original_price),
            "pick_up_price": float(self.pick_up_price) if self.pick_up_price is not None else None,
            "delivery_price": float(self.delivery_price) if self.delivery_price is not None else None,
            "consume_within": self.consume_within,
            "consume_within_type": self.consume_within_type,
            "expires_at": self.expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "update_count": self.update_count,
            "fresh_score": round(self.fresh_score, 2),
            "available_for_pickup": self.available_for_pickup,
            "available_for_delivery": self.available_for_delivery
        }

    def decrease_stock(self, quantity):
        if self.count < quantity:
            return False
        self.count -= quantity
        if self.count == 0:
            restaurant = Restaurant.query.get(self.restaurant_id)
            if restaurant and restaurant.listings > 0:
                restaurant.listings -= 1
                db.session.add(restaurant)
        db.session.add(self)
        return True

    def reject_associated_purchases(self):
        from .purchase_model import PurchaseStatus, Purchase
        active_purchases = Purchase.query.filter(
            db.and_(
                Purchase.listing_id == self.id,
                Purchase.status.in_(PurchaseStatus.active_statuses())
            )
        ).all()
        for purchase in active_purchases:
            try:
                purchase.update_status(PurchaseStatus.REJECTED)
                db.session.add(purchase)
            except ValueError as e:
                print(f"Error updating purchase {purchase.id}: {str(e)}")

    def is_expired(self):
        return datetime.now(UTC) > self.expires_at

    def update_expiry(self):
        current_time = datetime.now(UTC)
        if current_time > self.expires_at:
            return False

        total_lifetime = (self.expires_at - self.created_at).total_seconds() / 3600
        decrease_percentage = (6 / total_lifetime) * 100

        self.fresh_score = max(0, self.fresh_score - decrease_percentage)
        self.update_count += 1

        time_left = self.expires_at - current_time
        hours_left = time_left.total_seconds() / 3600

        if hours_left <= 6:
            self.delete_listing(self.id)
            return False

        if hours_left < 12:
            self.consume_within = round(hours_left)
            self.consume_within_type = 'HOURS'
        else:
            self.consume_within = round(hours_left / 24)
            self.consume_within_type = 'DAYS'

        db.session.add(self)
        return True

    @classmethod
    def delete_listing(cls, listing_id):
        try:
            listing = cls.query.get(listing_id)
            if not listing:
                return False, "Listing not found"
            listing.reject_associated_purchases()
            db.session.delete(listing)
            db.session.commit()
            return True, "Listing deleted successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting listing: {str(e)}"