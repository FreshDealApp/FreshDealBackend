from datetime import datetime, timezone, timedelta

from src.models import db
from src.models.restaurant_model import Restaurant
from src.models.restaurant_punishment_model import RestaurantPunishment, RefundRecord
from src.services.notification_service import NotificationService


class RestaurantPunishmentService:
    VALID_DURATIONS = {
        "THREE_DAYS": 3,
        "ONE_WEEK": 7,
        "ONE_MONTH": 30,
        "THREE_MONTHS": 90,
        "PERMANENT": None
    }

    @staticmethod
    def issue_punishment(restaurant_id: int, punishment_data: dict, support_user_id: int) -> tuple:
        try:
            restaurant = Restaurant.query.get(restaurant_id)
            if not restaurant:
                return {"success": False, "message": "Restaurant not found"}, 404

            duration_type = punishment_data.get('duration_type')
            if duration_type not in RestaurantPunishmentService.VALID_DURATIONS:
                return {"success": False, "message": "Invalid duration type"}, 400

            duration_days = RestaurantPunishmentService.VALID_DURATIONS[duration_type]
            start_date = datetime.now(timezone.utc)
            end_date = None if duration_days is None else start_date + timedelta(days=duration_days)

            punishment = RestaurantPunishment(
                restaurant_id=restaurant_id,
                reason=punishment_data.get('reason'),
                punishment_type='PERMANENT' if duration_days is None else 'TEMPORARY',
                duration_days=duration_days,
                start_date=start_date,
                end_date=end_date,
                created_by=support_user_id
            )

            db.session.add(punishment)
            db.session.commit()

            NotificationService.send_notification_to_user(
                user_id=restaurant.owner_id,
                title="Restaurant Punishment Issued",
                body=f"Your restaurant has been {duration_type.lower().replace('_', ' ')} suspended."
            )

            return {"success": True, "punishment_id": punishment.id}, 201

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}, 500

    @staticmethod
    def issue_refund(order_id: int, refund_data: dict, support_user_id: int) -> tuple:
        try:
            purchase = db.session.query(Purchase).get(order_id)
            if not purchase:
                return {"success": False, "message": "Order not found"}, 404

            refund = RefundRecord(
                restaurant_id=purchase.listing.restaurant_id,
                user_id=purchase.user_id,
                order_id=order_id,
                amount=refund_data.get('amount'),
                reason=refund_data.get('reason'),
                created_by=support_user_id
            )

            db.session.add(refund)
            db.session.commit()

            print(f"MOCK: Refund email sent to user {purchase.user_id} for amount ${refund.amount}")

            NotificationService.send_notification_to_user(
                user_id=purchase.user_id,
                title="Refund Issued",
                body=f"A refund of ${refund.amount} has been issued for your order."
            )

            refund.processed = True
            db.session.commit()
            return {"success": True, "refund_id": refund.id}, 201

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}, 500

    @staticmethod
    def check_restaurant_status(restaurant_id: int) -> dict:
        current_time = datetime.now(timezone.utc)
        active_punishment = RestaurantPunishment.query.filter(
            RestaurantPunishment.restaurant_id == restaurant_id,
            (
                    (RestaurantPunishment.punishment_type == 'PERMANENT') |
                    (
                            (RestaurantPunishment.punishment_type == 'TEMPORARY') &
                            (RestaurantPunishment.end_date > current_time)
                    )
            )
        ).first()

        if not active_punishment:
            return {"is_punished": False}

        return {
            "is_punished": True,
            "punishment_type": active_punishment.punishment_type,
            "end_date": active_punishment.end_date,
            "reason": active_punishment.reason
        }