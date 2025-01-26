import pytest
from flask import Flask
from flask.testing import FlaskClient
from unittest.mock import patch
from src.routes.search_routes import search_bp


@pytest.fixture
def app():
    # Create a Flask app instance
    app = Flask(__name__)
    app.register_blueprint(search_bp)
    return app


@pytest.fixture
def client(app: Flask):
    return app.test_client()


class TestSearchRoutes:

    @patch("src.services.search_service.search_restaurants")
    def test_search_restaurants_success(self, mock_search_restaurants: patch):
        # Arrange
        mock_search_restaurants.return_value = [{"id": 1, "name": "Restaurant A"}, {"id": 2, "name": "Restaurant B"}]
        query_params = {"type": "restaurant", "query": "Restaurant A"}

        # Act
        response = client.get("/search", query_string=query_params)

        # Assert
        assert response.status_code == 200
        response_json = response.get_json()
        assert response_json["success"] is True
        assert response_json["type"] == "restaurant"
        assert len(response_json["results"]) == 2
        assert response_json["results"][0]["name"] == "Restaurant A"

    @patch("src.services.search_service.search_listings")
    def test_search_listings_success(self, mock_search_listings: patch):
        # Arrange
        mock_search_listings.return_value = [{"id": 1, "title": "Listing 1"}, {"id": 2, "title": "Listing 2"}]
        query_params = {"type": "listing", "query": "Listing", "restaurant_id": 1}

        # Act
        response = client.get("/search", query_string=query_params)

        # Assert
        assert response.status_code == 200
        response_json = response.get_json()
        assert response_json["success"] is True
        assert response_json["type"] == "listing"
        assert len(response_json["results"]) == 2
        assert response_json["results"][0]["title"] == "Listing 1"

    def test_missing_query_param(self, client: FlaskClient):
        # Arrange
        query_params = {"type": "restaurant"}

        # Act
        response = client.get("/search", query_string=query_params)

        # Assert
        assert response.status_code == 400
        response_json = response.get_json()
        assert response_json["success"] is False
        assert response_json["message"] == "Query parameter is required"

    def test_invalid_search_type(self, client: FlaskClient):
        # Arrange
        query_params = {"type": "invalid", "query": "Restaurant A"}

        # Act
        response = client.get("/search", query_string=query_params)

        # Assert
        assert response.status_code == 400
        response_json = response.get_json()
        assert response_json["success"] is False
        assert response_json["message"] == "Invalid search type. Use 'restaurant' or 'listing'"

    def test_missing_restaurant_id_for_listing_search(self, client: FlaskClient):
        # Arrange
        query_params = {"type": "listing", "query": "Listing"}

        # Act
        response = client.get("/search", query_string=query_params)

        # Assert
        assert response.status_code == 400
        response_json = response.get_json()
        assert response_json["success"] is False
        assert response_json["message"] == "Restaurant ID is required for listing search"

    @patch("src.services.search_service.search_restaurants")
    def test_search_restaurants_error(self, mock_search_restaurants: patch):
        # Arrange
        mock_search_restaurants.side_effect = Exception("Internal error")
        query_params = {"type": "restaurant", "query": "Restaurant A"}

        # Act
        response = client.get("/search", query_string=query_params)

        # Assert
        assert response.status_code == 500
        response_json = response.get_json()
        assert response_json["success"] is False
        assert response_json["message"] == "An error occurred while performing search"
        assert "error" in response_json
