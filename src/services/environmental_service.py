from datetime import datetime, timedelta, UTC
from decimal import Decimal
from src.models import db, Purchase, PurchaseStatus, EnvironmentalContribution
from sqlalchemy import func


class EnvironmentalService:

    @staticmethod
    def calculate_co2_avoided_for_purchase(purchase):
        """
        Calculate CO2 avoided for a specific purchase based on food waste prevention
        Average CO2 avoided per kg of food waste prevented: 2.5 kg CO2 equivalent
        Assuming each food listing is about 0.5 kg on average
        """
        if purchase.status != PurchaseStatus.COMPLETED:
            return Decimal('0.00')

        # Base calculation: 0.5 kg food × 2.5 kg CO2/kg food × quantity
        base_co2_avoided = Decimal('1.25') * purchase.quantity

        return base_co2_avoided

    @staticmethod
    def record_contribution_for_purchase(purchase_id):
        """
        Record the environmental contribution for a completed purchase
        """
        # Check if contribution already recorded
        existing = EnvironmentalContribution.query.filter_by(purchase_id=purchase_id).first()
        if existing:
            return False

        purchase = Purchase.query.get(purchase_id)
        if not purchase or purchase.status != PurchaseStatus.COMPLETED:
            return False

        co2_avoided = EnvironmentalService.calculate_co2_avoided_for_purchase(purchase)

        contribution = EnvironmentalContribution(
            user_id=purchase.user_id,
            purchase_id=purchase_id,
            co2_avoided=co2_avoided
        )

        db.session.add(contribution)
        db.session.commit()
        return True

    @staticmethod
    def get_user_contributions(user_id):
        """
        Get user's environmental contributions (total and last month)
        """
        # Calculate total contributions
        total_query = db.session.query(
            func.sum(EnvironmentalContribution.co2_avoided)
        ).filter(
            EnvironmentalContribution.user_id == user_id
        )

        total_co2_avoided = total_query.scalar() or Decimal('0.00')

        # Calculate last month's contributions
        one_month_ago = datetime.now(UTC) - timedelta(days=30)

        monthly_query = db.session.query(
            func.sum(EnvironmentalContribution.co2_avoided)
        ).filter(
            EnvironmentalContribution.user_id == user_id,
            EnvironmentalContribution.created_at >= one_month_ago
        )

        monthly_co2_avoided = monthly_query.scalar() or Decimal('0.00')

        return {
            "success": True,
            "data": {
                "total_co2_avoided": float(total_co2_avoided),
                "monthly_co2_avoided": float(monthly_co2_avoided),
                "unit": "kg CO2 equivalent"
            }
        }

    @staticmethod
    def get_all_users_contributions():
        """
        Get all users' environmental contributions for leaderboard or analytics
        """
        total_query = db.session.query(
            EnvironmentalContribution.user_id,
            func.sum(EnvironmentalContribution.co2_avoided).label('total_co2_avoided')
        ).group_by(
            EnvironmentalContribution.user_id
        ).order_by(
            func.sum(EnvironmentalContribution.co2_avoided).desc()
        )

        one_month_ago = datetime.now(UTC) - timedelta(days=30)

        monthly_query = db.session.query(
            EnvironmentalContribution.user_id,
            func.sum(EnvironmentalContribution.co2_avoided).label('monthly_co2_avoided')
        ).filter(
            EnvironmentalContribution.created_at >= one_month_ago
        ).group_by(
            EnvironmentalContribution.user_id
        ).order_by(
            func.sum(EnvironmentalContribution.co2_avoided).desc()
        )

        total_results = {row.user_id: float(row.total_co2_avoided) for row in total_query.all()}
        monthly_results = {row.user_id: float(row.monthly_co2_avoided) for row in monthly_query.all()}

        all_user_ids = set(total_results.keys()).union(set(monthly_results.keys()))

        results = []
        for user_id in all_user_ids:
            results.append({
                "user_id": user_id,
                "total_co2_avoided": total_results.get(user_id, 0.0),
                "monthly_co2_avoided": monthly_results.get(user_id, 0.0)
            })

        # Sort by total CO2 avoided
        results.sort(key=lambda x: x["total_co2_avoided"], reverse=True)

        return {
            "success": True,
            "data": results,
            "unit": "kg CO2 equivalent"
        }