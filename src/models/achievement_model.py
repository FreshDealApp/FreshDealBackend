from . import db
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import enum


class AchievementType(str, enum.Enum):
    PURCHASE_COUNT = "PURCHASE_COUNT"
    WEEKLY_PURCHASE = "WEEKLY_PURCHASE"
    FIRST_PURCHASE = "FIRST_PURCHASE"
    REGULAR_COMMENTER = "REGULAR_COMMENTER"
    CUSTOM = "CUSTOM"


class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(100), nullable=False)
    description = db.Column(String(500), nullable=False)
    badge_image_url = db.Column(String(255), nullable=True)
    achievement_type = db.Column(Enum(AchievementType), nullable=False)
    threshold = db.Column(Integer, nullable=True)
    is_active = db.Column(Boolean, default=True, nullable=False)

    user_achievements = relationship('UserAchievement', back_populates='achievement')

    def __init__(self, name, description, achievement_type, badge_image_url=None, threshold=None):
        self.name = name
        self.description = description
        self.badge_image_url = badge_image_url
        self.achievement_type = achievement_type
        self.threshold = threshold
        self.is_active = True


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(Integer, db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    achievement = relationship('Achievement', back_populates='user_achievements')
    user = relationship('User', back_populates='achievements')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),
    )