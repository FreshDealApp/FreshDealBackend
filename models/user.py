from . import db
from sqlalchemy import Integer, String, CheckConstraint

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(80), nullable=False)
    email = db.Column(String(250), unique=True, nullable=True)
    phone_number = db.Column(String(15), unique=True, nullable=True)
    password = db.Column(String(1280), nullable=False)
    role = db.Column(String(20), nullable=False, default='customer')
    __table_args__ = (
        CheckConstraint("role IN ('customer', 'owner')", name='role_check'),
    )