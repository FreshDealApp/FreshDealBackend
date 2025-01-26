from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# First, import models with no dependencies on other models
from .user_model import User
from .address_model import CustomerAddress
from .restaurant_model import Restaurant

# Then import models that depend on the basic models
from .user_favorites_model import UserFavorites
from .user_cart_model import UserCart
from .listing_model import Listing

# Finally, import models that depend on multiple other models
from .purchase_model import Purchase
from .restaurant_comments_model import RestaurantComment
from .purchase_report import PurchaseReport
from .device import UserDevice

# Export all models
__all__ = [
    'db',
    'User',
    'CustomerAddress',
    'Restaurant',
    'Listing',
    'UserFavorites',
    'UserCart',
    'Purchase',
    'RestaurantComment',
    'PurchaseReport',
    'UserDevice'
]