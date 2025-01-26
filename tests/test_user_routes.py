import pytest
from unittest.mock import patch
from flask import Flask, jsonify
from flask_jwt_extended import create_access_token
from src.routes.user_routes import user_bp
from src.services.user_services import (
    fetch_user_data,
    change_password,
    change_username,
    change_email,
    add_favorite,
    remove_favorite,
    get_favorites
)

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(user_bp)
    app.config['JWT_SECRET_KEY'] = 'testsecret'
    return app

@pytest.fixture
def auth_headers(app):
    with app.app_context():
        access_token = create_access_token(identity=1)  # Mock user ID 1
        return {
            'Authorization': f'Bearer {access_token}'
        }

class TestUserRoutes:

    @patch('src.services.user_services.fetch_user_data')
    def test_get_user_success(self, mock_fetch_user_data, auth_headers, app):
        # Arrange
        mock_fetch_user_data.return_value = ({
            "user_data": {"id": 1, "name": "John", "email": "john@example.com"},
            "user_address_list": [{"id": 1, "title": "Home", "street": "123 St"}]
        }, None)

        # Act
        with app.test_client() as client:
            response = client.get('/user', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["user_data"]["name"] == "John"
        assert data["user_address_list"][0]["street"] == "123 St"

    @patch('src.services.user_services.change_password')
    def test_update_password_success(self, mock_change_password, auth_headers, app):
        # Arrange
        mock_change_password.return_value = (True, "Password updated successfully.")
        data = {"old_password": "oldpass", "new_password": "newpass"}

        # Act
        with app.test_client() as client:
            response = client.put('/user/password', json=data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json["message"] == "Password updated successfully."

    @patch('src.services.user_services.change_username')
    def test_update_username_success(self, mock_change_username, auth_headers, app):
        # Arrange
        mock_change_username.return_value = (True, "Username updated successfully.")
        data = {"username": "new_username"}

        # Act
        with app.test_client() as client:
            response = client.put('/user/username', json=data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json["message"] == "Username updated successfully."

    @patch('src.services.user_services.change_email')
    def test_update_email_success(self, mock_change_email, auth_headers, app):
        # Arrange
        mock_change_email.return_value = (True, "Email updated successfully.")
        data = {"old_email": "old@example.com", "new_email": "new@example.com"}

        # Act
        with app.test_client() as client:
            response = client.put('/user/email', json=data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json["message"] == "Email updated successfully."

    @patch('src.services.user_services.get_favorites')
    def test_get_favorites(self, mock_get_favorites, auth_headers, app):
        # Arrange
        mock_get_favorites.return_value = [1, 2, 3]  # Mocked favorite restaurant IDs

        # Act
        with app.test_client() as client:
            response = client.get('/user/favorites', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json["favorites"] == [1, 2, 3]

    @patch('src.services.user_services.add_favorite')
    def test_add_favorite_success(self, mock_add_favorite, auth_headers, app):
        # Arrange
        mock_add_favorite.return_value = (True, "Restaurant added to favorites.")
        data = {"restaurant_id": 1}

        # Act
        with app.test_client() as client:
            response = client.post('/user/favorites', json=data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        assert response.json["message"] == "Restaurant added to favorites."

    @patch('src.services.user_services.remove_favorite')
    def test_remove_favorite_success(self, mock_remove_favorite, auth_headers, app):
        # Arrange
        mock_remove_favorite.return_value = (True, "Restaurant removed from favorites.")
        data = {"restaurant_id": 1}

        # Act
        with app.test_client() as client:
            response = client.delete('/user/favorites', json=data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json["message"] == "Restaurant removed from favorites."

    @patch('src.services.purchase_service.get_user_active_orders_service')
    def test_get_user_active_orders(self, mock_get_user_active_orders_service, auth_headers, app):
        # Arrange
        mock_get_user_active_orders_service.return_value = jsonify({"active_orders": []})

        # Act
        with app.test_client() as client:
            response = client.get('/users/active-orders', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert "active_orders" in response.json
