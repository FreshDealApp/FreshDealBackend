from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .customerAddress import CustomerAddress
from .restaurant import Restaurant
