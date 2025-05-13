import unittest
from datetime import datetime, timedelta
from flask import Flask
from pytz import UTC
from decimal import Decimal
from src.models import db, Restaurant, Listing, User
from werkzeug.security import generate_password_hash
from app import create_app


class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456789@127.0.0.1:3306/freshdealtest'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        self.test_user = User(
            name="Test Owner",
            email="owner@test.com",
            phone_number="+1234567890",
            password=generate_password_hash("password123"),
            role="owner",
            email_verified=True
        )
        db.session.add(self.test_user)
        db.session.commit()

        self.test_restaurant = Restaurant(
            owner_id=self.test_user.id,
            restaurantName="Test Restaurant",
            restaurantDescription="Test Description",
            longitude=28.979530,
            latitude=41.015137,
            category="Test Category",
            workingDays="Monday,Tuesday",
            workingHoursStart="09:00",
            workingHoursEnd="22:00",
            pickup=True,
            delivery=True
        )
        db.session.add(self.test_restaurant)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_listing_expiry_update(self):
        current_time = datetime.now(UTC)

        listing = Listing(
            restaurant_id=self.test_restaurant.id,
            title="Test Listing",
            description="Test Description",
            image_url="http://test.com/image.jpg",
            original_price=Decimal('10.99'),
            pick_up_price=Decimal('9.99'),
            delivery_price=Decimal('12.99'),
            count=5,
            consume_within=24,
            consume_within_type='HOURS',
            expires_at=current_time + timedelta(hours=24),
            created_at=current_time,
            fresh_score=100.0,
            update_count=0
        )
        db.session.add(listing)
        db.session.commit()

        listing_id = listing.id

        listing.created_at = current_time - timedelta(hours=2)
        db.session.commit()

        listing.update_expiry()
        db.session.commit()

        updated_listing = Listing.query.get(listing_id)

        self.assertTrue(updated_listing.fresh_score < 100.0)
        self.assertEqual(updated_listing.update_count, 1)

    def test_listing_near_expiry_conversion(self):
        current_time = datetime.now(UTC)

        listing = Listing(
            restaurant_id=self.test_restaurant.id,
            title="Test Listing",
            description="Test Description",
            image_url="http://test.com/image.jpg",
            original_price=Decimal('10.99'),
            pick_up_price=Decimal('9.99'),
            delivery_price=Decimal('12.99'),
            count=5,
            consume_within=24,
            consume_within_type='HOURS',
            expires_at=current_time + timedelta(hours=11),
            created_at=current_time - timedelta(hours=13),
            fresh_score=100.0,
            update_count=0
        )
        db.session.add(listing)
        db.session.commit()

        listing_id = listing.id

        listing.update_expiry()
        db.session.commit()

        updated_listing = Listing.query.get(listing_id)

        self.assertEqual(updated_listing.consume_within_type, 'HOURS')
        self.assertTrue(updated_listing.consume_within < 12)

    def test_listing_deletion_when_expired(self):
        current_time = datetime.now(UTC)

        listing = Listing(
            restaurant_id=self.test_restaurant.id,
            title="Test Listing",
            description="Test Description",
            image_url="http://test.com/image.jpg",
            original_price=Decimal('10.99'),
            pick_up_price=Decimal('9.99'),
            delivery_price=Decimal('12.99'),
            count=5,
            consume_within=24,
            consume_within_type='HOURS',
            expires_at=current_time + timedelta(hours=5),
            created_at=current_time - timedelta(hours=19),
            fresh_score=100.0,
            update_count=0
        )
        db.session.add(listing)
        db.session.commit()

        listing_id = listing.id

        listing.update_expiry()
        db.session.commit()

        deleted_listing = Listing.query.get(listing_id)
        self.assertIsNone(deleted_listing)


if __name__ == '__main__':
    unittest.main()