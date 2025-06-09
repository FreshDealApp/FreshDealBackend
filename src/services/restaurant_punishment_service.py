from datetime import datetime, timezone, timedelta
from typing import Any

from src.models import db, User
from src.models.restaurant_model import Restaurant
from src.models.restaurant_punishment_model import RestaurantPunishment, RefundRecord
from src.models.purchase_model import Purchase
from src.models.purchase_report import PurchaseReport, ReportStatus
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
    def issue_punishment(restaurant_id: int, punishment_data: dict, support_user_id: int,
                         report_id: int = None) -> tuple:
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

            # Check for existing active punishment
            existing_punishment = RestaurantPunishment.query.filter(
                RestaurantPunishment.restaurant_id == restaurant_id,
                RestaurantPunishment.is_active == True,
                RestaurantPunishment.is_reverted == False
            ).first()

            if existing_punishment:
                # If punishment is temporary, extend it
                if existing_punishment.punishment_type == "TEMPORARY" and duration_days is not None:
                    # Add additional days to existing punishment
                    if existing_punishment.end_date:
                        existing_punishment.end_date = existing_punishment.end_date + timedelta(days=duration_days)
                        existing_punishment.duration_days += duration_days
                        db.session.commit()

                        # Update report status if provided
                        if report_id:
                            report = PurchaseReport.query.get(report_id)
                            if report:
                                report.status = ReportStatus.RESOLVED
                                report.resolved_at = datetime.now(timezone.utc)
                                report.resolved_by = support_user_id
                                report.punishment_id = existing_punishment.id
                                db.session.commit()

                        return {
                            "success": True,
                            "punishment_id": existing_punishment.id,
                            "message": "Punishment duration extended"
                        }, 200

                # If existing punishment is permanent, no changes needed
                if existing_punishment.punishment_type == "PERMANENT":
                    # Just update report status if provided
                    if report_id:
                        report = PurchaseReport.query.get(report_id)
                        if report:
                            report.status = ReportStatus.RESOLVED
                            report.resolved_at = datetime.now(timezone.utc)
                            report.resolved_by = support_user_id
                            report.punishment_id = existing_punishment.id
                            db.session.commit()

                    return {
                        "success": True,
                        "punishment_id": existing_punishment.id,
                        "message": "Restaurant already has a permanent punishment"
                    }, 200

            # Create new punishment
            punishment = RestaurantPunishment(
                restaurant_id=restaurant_id,
                reason=punishment_data.get('reason'),
                punishment_type='PERMANENT' if duration_days is None else 'TEMPORARY',
                duration_days=duration_days,
                start_date=start_date,
                end_date=end_date,
                created_by=support_user_id,
                is_active=True
            )

            db.session.add(punishment)

            # Update report if provided
            if report_id:
                report = PurchaseReport.query.get(report_id)
                if report:
                    report.status = ReportStatus.RESOLVED
                    report.resolved_at = datetime.now(timezone.utc)
                    report.resolved_by = support_user_id
                    report.punishment_id = punishment.id

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
    def revert_punishment(punishment_id: int, reversion_data: dict, support_user_id: int) -> tuple:
        try:
            punishment = RestaurantPunishment.query.get(punishment_id)
            if not punishment:
                return {"success": False, "message": "Punishment not found"}, 404

            if punishment.is_reverted:
                return {"success": False, "message": "This punishment has already been reverted"}, 400

            punishment.is_reverted = True
            punishment.is_active = False
            punishment.reverted_by = support_user_id
            punishment.reverted_at = datetime.now(timezone.utc)
            punishment.reversion_reason = reversion_data.get('reason', 'No reason provided')

            db.session.commit()

            NotificationService.send_notification_to_user(
                user_id=punishment.restaurant.owner_id,
                title="Restaurant Punishment Reverted",
                body=f"The punishment for your restaurant has been reverted."
            )

            return {"success": True, "message": "Punishment successfully reverted"}, 200

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

            print(f"MOCK: Refund email sent to user {purchase.user_id} for amount {refund.amount}")

            NotificationService.send_notification_to_user(
                user_id=purchase.user_id,
                title="Refund Issued",
                body=f"A refund of {refund.amount} has been issued for your order."
            )

            refund.processed = True
            db.session.commit()
            return {"success": True, "refund_id": refund.id}, 201

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}, 500

    @staticmethod
    def check_restaurant_status(restaurant_id: int) -> tuple[dict[str, str | bool], int] | tuple[
        dict[str, bool | None | dict[str, Any | None] | Any], int]:
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return {"success": False, "message": "Restaurant not found"}, 404

        is_active = restaurant.is_active

        # Get punishment details if inactive
        punishment_details = None
        if not is_active:
            active_punishment = RestaurantPunishment.query.filter(
                RestaurantPunishment.restaurant_id == restaurant_id,
                RestaurantPunishment.is_active == True,
                RestaurantPunishment.is_reverted == False
            ).first()

            if active_punishment:
                punishment_details = {
                    "punishment_id": active_punishment.id,
                    "type": active_punishment.punishment_type,
                    "start_date": active_punishment.start_date.isoformat(),
                    "end_date": active_punishment.end_date.isoformat() if active_punishment.end_date else None,
                    "reason": active_punishment.reason
                }

        return {
            "success": True,
            "is_active": is_active,
            "punishment": punishment_details
        }, 200


    @staticmethod
    def get_punishment_history(restaurant_id: int) -> tuple:
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return {"success": False, "message": "Restaurant not found"}, 404

        punishments = RestaurantPunishment.query.filter_by(
            restaurant_id=restaurant_id
        ).order_by(RestaurantPunishment.created_at.desc()).all()

        punishment_history = []
        for punishment in punishments:
            creator = db.session.get(User, punishment.created_by)
            reverter = db.session.get(User, punishment.reverted_by) if punishment.reverted_by else None

            punishment_data = {
                "id": punishment.id,
                "type": punishment.punishment_type,
                "duration_days": punishment.duration_days,
                "start_date": punishment.start_date.isoformat(),
                "end_date": punishment.end_date.isoformat() if punishment.end_date else None,
                "reason": punishment.reason,
                "is_active": punishment.is_active,
                "is_reverted": punishment.is_reverted,
                "created_by": {
                    "id": creator.id,
                    "name": creator.name if creator else "Unknown"
                },
                "created_at": punishment.created_at.isoformat()
            }

            if punishment.is_reverted and reverter:
                punishment_data["reverted_info"] = {
                    "reverted_by": {
                        "id": reverter.id,
                        "name": reverter.name
                    },
                    "reverted_at": punishment.reverted_at.isoformat(),
                    "reason": punishment.reversion_reason
                }

            punishment_history.append(punishment_data)

        return {
            "success": True,
            "restaurant_name": restaurant.restaurantName,
            "punishment_history": punishment_history
        }, 200