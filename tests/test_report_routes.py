# tests/test_report_routes.py

import pytest
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from src.routes.report_routes import report_bp
from src.services.report_service import create_purchase_report_service, get_user_reports_service
from unittest.mock import patch

# Create Flask app instance for testing
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "supersecret"
    app.register_blueprint(report_bp)
    return app

# Create a mock JWT token for testing
@pytest.fixture
def mock_jwt():
    return "mock-jwt-token"

# Mock the database session and services
@pytest.fixture
def mock_db():
    # Simulating the behavior of the database for testing
    # This should be adjusted based on how your actual database setup is mocked
    with patch("src.services.report_service.create_purchase_report_service") as mock_create_service:
        with patch("src.services.report_service.get_user_reports_service") as mock_get_reports_service:
            yield mock_create_service, mock_get_reports_service

# Test the POST /report endpoint
def test_create_report(mock_db, app, mock_jwt):
    mock_create_service, mock_get_reports_service = mock_db

    # Prepare mock return value for create_purchase_report_service
    mock_create_service.return_value = {"message": "Report created successfully"}, 201

    # Simulate a POST request with a valid payload
    with app.test_client() as client:
        response = client.post(
            "/report",
            json={
                "purchase_id": 1,
                "description": "Test Report",
                "image_url": "http://example.com/image.jpg"
            },
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

    assert response.status_code == 201
    assert response.json["message"] == "Report created successfully"

# Test the GET /report endpoint
def test_get_user_reports(mock_db, app, mock_jwt):
    mock_create_service, mock_get_reports_service = mock_db

    # Prepare mock return value for get_user_reports_service
    mock_get_reports_service.return_value = [{"purchase_id": 1, "description": "Test Report"}], 200

    # Simulate a GET request to fetch reports
    with app.test_client() as client:
        response = client.get(
            "/report",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) == 1
    assert response.json[0]["description"] == "Test Report"

# Test for invalid POST /report (missing purchase_id)
def test_create_report_missing_purchase_id(mock_db, app, mock_jwt):
    mock_create_service, mock_get_reports_service = mock_db

    # Simulate a POST request with missing purchase_id
    with app.test_client() as client:
        response = client.post(
            "/report",
            json={
                "description": "Test Report",
                "image_url": "http://example.com/image.jpg"
            },
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

    assert response.status_code == 400
    assert response.json["message"] == "Missing required fields (purchase_id, description)."

# Test for invalid GET /report (simulate internal server error)
def test_get_user_reports_server_error(mock_db, app, mock_jwt):
    mock_create_service, mock_get_reports_service = mock_db

    # Simulate a server error in the service layer
    mock_get_reports_service.side_effect = Exception("Database error")

    # Simulate a GET request to fetch reports
    with app.test_client() as client:
        response = client.get(
            "/report",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

    assert response.status_code == 500
    assert response.json["message"] == "An error occurred"
