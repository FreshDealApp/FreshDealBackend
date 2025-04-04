from . import db
from sqlalchemy import Integer

class RestaurantBadgePoints(db.Model):
    __tablename__ = 'restaurant_badge_points'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    restaurantID = db.Column(Integer, db.ForeignKey('restaurants.id'), nullable=False)
    freshPoint = db.Column(Integer, nullable=False, default=0)
    fastDeliveryPoint = db.Column(Integer, nullable=False, default=0)
    customerFriendlyPoint = db.Column(Integer, nullable=False, default=0)
