import os
import pytest
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import MultiDict
from flask import Flask
from src.models import db, Restaurant
from src.services.restaurant_service import create_restaurant_service, get_restaurants_service

@pytest.fixture
def app():
    """Create a Flask app instance for testing."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # In-memory database
    app.config["TESTING"] = True
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


def test_create_restaurant_success(app):
    """Test successful creation of a restaurant."""
    form = MultiDict({
        "restaurantName": "Test Restaurant",
        "restaurantDescription": "A nice place to eat.",
        "longitude": "34.0522",
        "latitude": "-118.2437",
        "category": "Italian",
        "workingHoursStart": "09:00",
        "workingHoursEnd": "22:00",
        "listings": "10",
        "pickup": "true",
        "delivery": "true",
        "deliveryFee": "5.99",
        "minOrderAmount": "20.00",
        "maxDeliveryDistance": "15",
    })
    files = {}  # No file uploaded

    # Mock the url_for function
    url_for_func = MagicMock(return_value="http://example.com/uploads/test.jpg")

    with app.app_context():
        response, status_code = create_restaurant_service(1, form, files, url_for_func)

        assert status_code == 201
        assert response["success"] is True
        assert response["message"] == "Restaurant added successfully!"

        # Verify restaurant exists in the database
        restaurant = Restaurant.query.first()
        assert restaurant is not None
        assert restaurant.restaurantName == "Test Restaurant"
        assert restaurant.category == "Italian"
        assert restaurant.pickup is True
        assert restaurant.delivery is True


def test_create_restaurant_missing_required_fields(app):
    """Test failure when required fields are missing."""
    form = MultiDict({
        "longitude": "34.0522",
        "latitude": "-118.2437",
    })
    files = {}

    with app.app_context():
        response, status_code = create_restaurant_service(1, form, files, MagicMock())
        assert status_code == 400
        assert response["success"] is False
        assert response["message"] == "Restaurant name is required"


@patch("src.services.restaurant_service.allowed_file")
@patch("src.services.restaurant_service.secure_filename")
def test_create_restaurant_with_image(mock_secure_filename, mock_allowed_file, app):
    """Test restaurant creation with an image file."""
    mock_allowed_file.return_value = True
    mock_secure_filename.return_value = "test_image.jpg"

    form = MultiDict({
        "restaurantName": "Test Restaurant",
        "longitude": "34.0522",
        "latitude": "-118.2437",
        "category": "Fast Food",
    })
    files = {
        "image": MagicMock(filename="image.jpg", save=MagicMock())
    }

    url_for_func = MagicMock(return_value="http://example.com/uploads/test_image.jpg")

    with app.app_context():
        response, status_code = create_restaurant_service(1, form, files, url_for_func)

        assert status_code == 201
        assert response["success"] is True
        assert response["restaurant"]["image_url"] == "http://example.com/uploads/test_image.jpg"


def test_get_restaurants_service(app):
    """Test retrieving restaurants for a specific owner."""
    # Insert a restaurant into the database
    restaurant = Restaurant(
        owner_id=1,
        restaurantName="Test Restaurant",
        longitude=34.0522,
        latitude=-118.2437,
        category="Italian"
    )
    with app.app_context():
        db.session.add(restaurant)
        db.session.commit()

        response, status_code = get_restaurants_service(1)

        assert status_code == 200
        assert len(response) == 1
        assert response[0]["restaurantName"] == "Test Restaurant"


def test_get_restaurants_service_no_restaurants(app):
    """Test retrieving restaurants when none exist."""
    with app.app_context():
        response, status_code = get_restaurants_service(1)
        assert status_code == 404
        assert response["message"] == "No restaurant found for the owner"
