from sqlalchemy.orm import relationship
from . import db
from datetime import datetime, UTC

class UserDevice(db.Model):
    __tablename__ = 'user_devices'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    push_token = db.Column(db.String(255), nullable=False)
    web_push_token = db.Column(db.Text, nullable=True)
    device_type = db.Column(db.String(20))
    platform = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    last_used = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    is_active = db.Column(db.Boolean, default=True)

    user = relationship('User', back_populates='devices')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'push_token', name='unique_user_device'),
    )