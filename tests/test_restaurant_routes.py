# tests/test_restaurant_routes.py

import pytest
from unittest.mock import patch
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from src.models import db, User, Restaurant
from src.routes.restaurant_routes import restaurant_bp

# Create a test Flask app
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"  # In-memory DB for testing
    app.config['JWT_SECRET_KEY'] = 'testsecret'
    app.register_blueprint(restaurant_bp)
    db.init_app(app)
    JWTManager(app)
    return app

# Create a test client
@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

# Create a test user (owner) for authentication
@pytest.fixture
def test_user():
    user = User(username="testuser", email="test@example.com", role="owner")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_restaurant(test_user):
    restaurant = Restaurant(
        name="Test Restaurant",
        description="A test restaurant",
        owner_id=test_user.id,
        category="Fast Food"
    )
    db.session.add(restaurant)
    db.session.commit()
    return restaurant

# Test the create_restaurant route
def test_create_restaurant(client, test_user):
    """
    Test creating a restaurant by a valid owner.
    """

    # Simulate JWT authentication
    with patch("flask_jwt_extended.get_jwt_identity", return_value=test_user.id):
        response = client.post("/restaurants", json={
            "restaurantName": "New Test Restaurant",
            "longitude": 123.456,
            "latitude": 78.910,
            "category": "Italian"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["message"] == "Restaurant added successfully."

# Test the get_restaurants route
def test_get_restaurants(client, test_user, test_restaurant):
    """
    Test fetching all restaurants for the authenticated owner.
    """
    with patch("flask_jwt_extended.get_jwt_identity", return_value=test_user.id):
        response = client.get("/restaurants")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data["restaurants"], list)
        assert len(data["restaurants"]) > 0

# Test the get_restaurant route
def test_get_restaurant(client, test_restaurant):
    """
    Test fetching a specific restaurant by ID.
    """
    response = client.get(f"/restaurants/{test_restaurant.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == test_restaurant.name

# Test the delete_restaurant route
def test_delete_restaurant(client, test_user, test_restaurant):
    """
    Test deleting a restaurant by the owner.
    """
    with patch("flask_jwt_extended.get_jwt_identity", return_value=test_user.id):
        response = client.delete(f"/restaurants/{test_restaurant.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Restaurant successfully deleted."

# Test the get_uploaded_file route
def test_get_uploaded_file(client):
    """
    Test fetching an uploaded file (assuming file upload exists).
    """
    response = client.get("/uploads/testimage.jpg")
    assert response.status_code == 404  # Assuming file does not exist

# Test the get_restaurants_proximity route
def test_get_restaurants_proximity(client):
    """
    Test getting restaurants by proximity.
    """
    response = client.post("/restaurants/proximity", json={
        "latitude": 40.730610,
        "longitude": -73.935242,
        "radius": 10
    })
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data["restaurants"], list)

# Test adding a comment to a restaurant
def test_add_comment(client, test_user, test_restaurant):
    """
    Test adding a comment to a restaurant.
    """
    with patch("flask_jwt_extended.get_jwt_identity", return_value=test_user.id):
        response = client.post(f"/restaurants/{test_restaurant.id}/comments", json={
            "comment": "Great food!",
            "rating": 5,
            "purchase_id": 1
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["message"] == "Comment added successfully."

# Test the update_restaurant route
def test_update_restaurant(client, test_user, test_restaurant):
    """
    Test updating a restaurant's details.
    """
    with patch("flask_jwt_extended.get_jwt_identity", return_value=test_user.id):
        response = client.put(f"/restaurants/{test_restaurant.id}", json={
            "restaurantName": "Updated Restaurant",
            "category": "Fine Dining"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Restaurant updated successfully."
