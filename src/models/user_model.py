# models/user.py
from sqlalchemy.orm import relationship
from . import db
from sqlalchemy import Integer, String, CheckConstraint, Boolean


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(80), nullable=False)
    email = db.Column(String(250), unique=True, nullable=True)
    phone_number = db.Column(String(15), unique=True, nullable=True)
    password = db.Column(String(1280), nullable=False)
    role = db.Column(String(20), nullable=False, default='customer')
    email_verified = db.Column(Boolean, nullable=False, default=False)
    __table_args__ = (
        CheckConstraint("role IN ('customer', 'owner')", name='role_check'),
    )

    # Relationships
    purchases = relationship('Purchase', back_populates='user')
    comments = relationship('RestaurantComment', back_populates='user')
    devices = relationship('UserDevice', back_populates='user', lazy=True)

    # Other columns
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)