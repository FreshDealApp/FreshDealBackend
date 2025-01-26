# models/user_device.py
from sqlalchemy.orm import relationship

from . import db
from datetime import datetime

class UserDevice(db.Model):
    __tablename__ = 'user_devices'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    push_token = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(20))  # 'ios' or 'android'
    platform = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Define the relationship from this side
    user = relationship('User', back_populates='devices')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'push_token', name='unique_user_device'),
    )