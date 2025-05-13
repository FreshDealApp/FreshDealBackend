from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user_model import User
from .address_model import CustomerAddress
from .restaurant_model import Restaurant
from .user_favorites_model import UserFavorites
from .user_cart_model import UserCart
from .listing_model import Listing
from .discount_earned import DiscountEarned
from .restaurant_badge_points_model import RestaurantBadgePoints
from .restaurant_comments_model import RestaurantComment
from .purchase_model import Purchase, PurchaseStatus
from .purchase_report import PurchaseReport
from .device import UserDevice
from .achievement_model import Achievement, UserAchievement, AchievementType
from .comment_badges_model import CommentBadge
from .restaurant_punishment_model import RestaurantPunishment, RefundRecord
from .enviromental_contribution_model import EnvironmentalContribution

__all__ = [
    'db',
    'User',
    'CustomerAddress',
    'Restaurant',
    'Listing',
    'UserFavorites',
    'UserCart',
    'Purchase',
    'PurchaseStatus',
    'RestaurantComment',
    'PurchaseReport',
    'UserDevice',
    'DiscountEarned',
    'Achievement',
    'UserAchievement',
    'AchievementType',
    'RestaurantBadgePoints',
    'CommentBadge',
    'RestaurantPunishment',
    'RefundRecord',
    'EnvironmentalContribution',
]