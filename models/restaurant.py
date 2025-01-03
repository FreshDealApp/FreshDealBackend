from . import db
from sqlalchemy import Integer, String, DECIMAL
from sqlalchemy.orm import validates

class Restaurant(db.Model):
    __tablename__ = 'restaurants'

    id = db.Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    owner_id = db.Column(Integer, db.ForeignKey('users.id'), nullable=False)

    restaurantName = db.Column(String(80), nullable=False)
    restaurantDescription = db.Column(String(500), nullable=True)
    longitude = db.Column(DECIMAL(9, 6), nullable=False)
    latitude = db.Column(DECIMAL(9, 6), nullable=False)
    category = db.Column(String(80), nullable=False)

    workingDays = db.Column(String(56), nullable=True)
    workingHoursStart = db.Column(String(5), nullable=True)
    workingHoursEnd = db.Column(String(5), nullable=True)

    listings = db.Column(Integer, nullable=False, default=0)

    rating = db.Column(DECIMAL(3,2), nullable=True)
    ratingCount = db.Column(Integer, nullable=False, default=0)

    @validates('workingDays')
    def validate_working_days(self, key, workingDays):
        valid_days = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}
        days_list = workingDays.split(',')

        if not all(day in valid_days for day in days_list):
            raise ValueError(f"Working days must be one of {', '.join(valid_days)}")

        return workingDays

    @validates('workingHoursStart', 'workingHoursEnd')
    def validate_working_hours(self, key, value):
        try:
            hours, minutes = map(int, value.split(':'))
            if not (0 <= hours < 24) or not (0 <= minutes < 60):
                raise ValueError("Time must be in HH:MM format with valid hour (00-23) and minute (00-59).")
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM (24-hour format).")

        return value

    @validates('rating')
    def validate_rating(self, key, rating):
        if rating is not None and not (0 <= rating <= 5):
            raise ValueError("Rating must be between 0.00 and 5.00.")
        return rating
