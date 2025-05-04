from datetime import datetime, timedelta, UTC
from src.models import db, UserAchievement, Achievement, AchievementType, Purchase, PurchaseStatus, RestaurantComment


class AchievementService:
    @staticmethod
    def initialize_achievements():
        """
        Initialize default achievements if they don't exist
        """
        # Check if achievements already exist
        if Achievement.query.count() > 0:
            return

        # Create default achievements
        default_achievements = [
            Achievement(
                name="First Purchase",
                description="Made your first purchase on FreshDeal",
                achievement_type=AchievementType.FIRST_PURCHASE,
                badge_image_url="/static/badges/first_purchase.png",
                threshold=1
            ),
            Achievement(
                name="Regular Buyer",
                description="Completed 5 purchases",
                achievement_type=AchievementType.PURCHASE_COUNT,
                badge_image_url="/static/badges/regular_buyer.png",
                threshold=5
            ),
            Achievement(
                name="Loyal Customer",
                description="Completed 25 purchases",
                achievement_type=AchievementType.PURCHASE_COUNT,
                badge_image_url="/static/badges/loyal_customer.png",
                threshold=25
            ),
            Achievement(
                name="FreshDeal VIP",
                description="Completed 50 purchases",
                achievement_type=AchievementType.PURCHASE_COUNT,
                badge_image_url="/static/badges/vip_customer.png",
                threshold=50
            ),
            Achievement(
                name="FreshDeal Legend",
                description="Completed 100 purchases",
                achievement_type=AchievementType.PURCHASE_COUNT,
                badge_image_url="/static/badges/legend_customer.png",
                threshold=100
            ),
            Achievement(
                name="Weekly Champion",
                description="Made 5 purchases in a week",
                achievement_type=AchievementType.WEEKLY_PURCHASE,
                badge_image_url="/static/badges/weekly_champion.png",
                threshold=5
            ),
            Achievement(
                name="Regular Commenter",
                description="Made 100 comments in 90 days",
                achievement_type=AchievementType.REGULAR_COMMENTER,
                badge_image_url="/static/badges/regular_commenter.png",
                threshold=100
            )
        ]

        db.session.add_all(default_achievements)
        db.session.commit()

    @staticmethod
    def check_and_award_achievements(user_id):
        """
        Check if the user qualifies for any achievements and award them
        """
        newly_earned = []

        # Check first purchase achievement
        newly_earned.extend(AchievementService._check_first_purchase(user_id))

        # Check purchase count achievements (5, 25, 50, 100)
        newly_earned.extend(AchievementService._check_purchase_count_achievements(user_id))

        # Check weekly purchase achievement (5 purchases in a week)
        newly_earned.extend(AchievementService._check_weekly_purchase_achievement(user_id))

        # Check comment achievement (100 comments in 90 days)
        newly_earned.extend(AchievementService._check_comment_achievement(user_id))

        return newly_earned

    @staticmethod
    def _check_first_purchase(user_id):
        """Check and award first purchase achievement"""
        newly_earned = []

        # Get the first purchase achievement
        first_purchase_achievement = Achievement.query.filter_by(
            achievement_type=AchievementType.FIRST_PURCHASE
        ).first()

        if not first_purchase_achievement:
            return newly_earned

        # Check if user already has this achievement
        existing = UserAchievement.query.filter_by(
            user_id=user_id,
            achievement_id=first_purchase_achievement.id
        ).first()

        if existing:
            return newly_earned

        # Check if user has any completed purchases
        purchase_count = Purchase.query.filter(
            Purchase.user_id == user_id,
            Purchase.status == PurchaseStatus.COMPLETED
        ).count()

        if purchase_count >= 1:
            # Award the achievement
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=first_purchase_achievement.id
            )
            db.session.add(user_achievement)
            db.session.commit()
            newly_earned.append(first_purchase_achievement)

        return newly_earned

    @staticmethod
    def _check_purchase_count_achievements(user_id):
        """Check and award purchase count achievements (5, 25, 50, 100)"""
        newly_earned = []

        # Get all purchase count achievements
        purchase_count_achievements = Achievement.query.filter_by(
            achievement_type=AchievementType.PURCHASE_COUNT
        ).order_by(Achievement.threshold).all()

        if not purchase_count_achievements:
            return newly_earned

        # Get user's completed purchase count
        purchase_count = Purchase.query.filter(
            Purchase.user_id == user_id,
            Purchase.status == PurchaseStatus.COMPLETED
        ).count()

        # Check each achievement threshold
        for achievement in purchase_count_achievements:
            if purchase_count >= achievement.threshold:
                # Check if user already has this achievement
                existing = UserAchievement.query.filter_by(
                    user_id=user_id,
                    achievement_id=achievement.id
                ).first()

                if not existing:
                    # Award the achievement
                    user_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id
                    )
                    db.session.add(user_achievement)
                    db.session.commit()
                    newly_earned.append(achievement)

        return newly_earned

    @staticmethod
    def _check_weekly_purchase_achievement(user_id):

        newly_earned = []


        weekly_achievement = Achievement.query.filter_by(
            achievement_type=AchievementType.WEEKLY_PURCHASE
        ).first()

        if not weekly_achievement:
            return newly_earned


        existing = UserAchievement.query.filter_by(
            user_id=user_id,
            achievement_id=weekly_achievement.id
        ).first()


        if not existing:
            one_week_ago = datetime.now(UTC) - timedelta(days=7)


            weekly_purchase_count = Purchase.query.filter(
                Purchase.user_id == user_id,
                Purchase.status == PurchaseStatus.COMPLETED,
                Purchase.purchase_date >= one_week_ago
            ).count()

            if weekly_purchase_count >= weekly_achievement.threshold:

                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=weekly_achievement.id
                )
                db.session.add(user_achievement)
                db.session.commit()
                newly_earned.append(weekly_achievement)

        return newly_earned

    @staticmethod
    def _check_comment_achievement(user_id):

        newly_earned = []

        comment_achievement = Achievement.query.filter_by(
            achievement_type=AchievementType.REGULAR_COMMENTER
        ).first()

        if not comment_achievement:
            return newly_earned

        existing = UserAchievement.query.filter_by(
            user_id=user_id,
            achievement_id=comment_achievement.id
        ).first()

        if not existing:
            ninety_days_ago = datetime.now(UTC) - timedelta(days=90)

            comment_count = db.session.query(RestaurantComment).filter(
                RestaurantComment.user_id == user_id,
                RestaurantComment.timestamp >= ninety_days_ago
            ).count()

            if comment_count >= comment_achievement.threshold:
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=comment_achievement.id
                )
                db.session.add(user_achievement)
                db.session.commit()
                newly_earned.append(comment_achievement)

        return newly_earned

    @staticmethod
    def get_user_achievements(user_id):
        """Get all achievements earned by a user"""
        user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()

        achievements = []
        for ua in user_achievements:
            achievements.append({
                "id": ua.achievement.id,
                "name": ua.achievement.name,
                "description": ua.achievement.description,
                "badge_image_url": ua.achievement.badge_image_url,
                "earned_at": ua.earned_at.isoformat(),
                "achievement_type": ua.achievement.achievement_type.value
            })

        return achievements

    @staticmethod
    def get_available_achievements():
        """Get all available achievements"""
        achievements = Achievement.query.filter_by(is_active=True).all()

        result = []
        for achievement in achievements:
            result.append({
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "badge_image_url": achievement.badge_image_url,
                "achievement_type": achievement.achievement_type.value,
                "threshold": achievement.threshold
            })

        return result