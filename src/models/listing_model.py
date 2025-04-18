from sqlalchemy.orm import relationship
from . import db, Restaurant
from sqlalchemy import Integer, String, ForeignKey, DECIMAL



class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = db.Column(
        Integer,
        ForeignKey('restaurants.id'),  # <-- remove ondelete='CASCADE'
        nullable=False
    )
    title = db.Column(String(255), nullable=False)
    description = db.Column(String(1000), nullable=True)
    image_url = db.Column(String(2083), nullable=True)  # URL for the image
    count = db.Column(Integer, nullable=False, default=1)  # Default count set to 1
    original_price = db.Column(DECIMAL(10, 2), nullable=False)
    pick_up_price = db.Column(DECIMAL(10, 2), nullable=True)
    delivery_price = db.Column(DECIMAL(10, 2), nullable=True)
    consume_within = db.Column(Integer, nullable=False)  # Number of days to consume the item

    # Dynamically calculated based on the associated Restaurant's pickup/delivery availability
    available_for_pickup = db.Column(db.Boolean, nullable=True)
    available_for_delivery = db.Column(db.Boolean, nullable=True)

    purchases = relationship('Purchase', back_populates='listing')

    @staticmethod
    def sync_availability(listing, restaurant):
        """
        Syncs the listing's availability with the restaurant's settings.
        """
        listing.available_for_pickup = restaurant.pickup
        listing.available_for_delivery = restaurant.delivery

    @classmethod
    def create(cls, **kwargs):
        """
        Override the creation method to automatically set pickup and delivery availability.
        """
        restaurant = db.session.query(Restaurant).get(kwargs['restaurant_id'])
        if not restaurant:
            raise ValueError("Invalid restaurant ID.")
        listing = cls(**kwargs)
        cls.sync_availability(listing, restaurant)
        return listing

    def to_dict(self):
        """
        Serializes the Listing object to a dictionary.
        """
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
            "available_for_pickup": self.available_for_pickup,
            "available_for_delivery": self.available_for_delivery
        }

    def decrease_stock(self, quantity):
        """
        Decreases the listing stock and updates restaurant listing count if needed.
        Returns True if successful, False if not enough stock.
        """
        if self.count < quantity:
            return False

        self.count -= quantity

        # If count reaches 0, decrease restaurant's listings count
        if self.count == 0:
            restaurant = Restaurant.query.get(self.restaurant_id)
            if restaurant and restaurant.listings > 0:
                restaurant.listings -= 1
                db.session.add(restaurant)

        db.session.add(self)
        return True

    def reject_associated_purchases(self):
        """
        Rejects all active purchases associated with this listing before deletion
        """
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
                # Log the error but continue with other purchases
                print(f"Error updating purchase {purchase.id}: {str(e)}")

    @classmethod
    def delete_listing(cls, listing_id):
        """
        Safely delete a listing by first rejecting all associated active purchases
        """
        print(f"Deleting listing: {listing_id}")
        try:
            listing = cls.query.get(listing_id)
            if not listing:
                print(f"Listing not found: {listing_id}")
                return False, "Listing not found"

            # First reject all associated active purchases
            listing.reject_associated_purchases()

            # Now delete the listing
            db.session.delete(listing)
            db.session.commit()
            print(f"Listing deleted: {listing_id}")
            return True, "Listing deleted successfully"
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting listing: {str(e)}")
            return False, f"Error deleting listing: {str(e)}"