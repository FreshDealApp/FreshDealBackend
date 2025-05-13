from . import db
from sqlalchemy import Integer, DECIMAL, DateTime
from datetime import datetime, UTC

class EnvironmentalContribution(db.Model):
    __tablename__ = 'environmental_contributions'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer, db.ForeignKey('users.id'), nullable=False)
    purchase_id = db.Column(Integer, db.ForeignKey('purchases.id'), nullable=False, unique=True)
    co2_avoided = db.Column(DECIMAL(10, 2), nullable=False)
    created_at = db.Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        db.Index('idx_environmental_contribution_user', 'user_id'),
        db.Index('idx_environmental_contribution_date', 'created_at'),
    )