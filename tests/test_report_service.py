# tests/test_report_service.py

import pytest
from unittest.mock import patch
from src.services.report_service import create_purchase_report_service, get_user_reports_service
from src.models import db, Purchase, PurchaseReport
from datetime import datetime

# Mock the Purchase model to simulate the database interaction
@pytest.fixture
def mock_purchase():
    # Mock a valid purchase object
    return Purchase(id=1, user_id=1, listing=None)

@pytest.fixture
def mock_report():
    # Mock a valid report object
    return PurchaseReport(id=1, user_id=1, purchase_id=1, description="Test report", image_url="http://example.com/image.jpg")

@pytest.fixture
def mock_db():
    # Simulate the DB setup and teardown process
    with patch("src.models.db.session.add"), patch("src.models.db.session.commit"), patch("src.models.db.session.rollback"):
        yield

# Test the create_purchase_report_service
def test_create_purchase_report_service(mock_db, mock_purchase):
    """
    Test creating a new purchase report.
    Verifies that the report is created successfully and that proper validations are in place.
    """

    # Test case when purchase does not exist
    with patch("src.services.report_service.Purchase.query.filter_by") as mock_query:
        mock_query.return_value.first.return_value = None
        response, status = create_purchase_report_service(1, 1, "http://example.com/image.jpg", "Test report")
        assert status == 404
        assert response["message"] == "Purchase not found or does not belong to the user."

    # Test case when user has already reported the purchase
    with patch("src.services.report_service.Purchase.query.filter_by") as mock_query, patch("src.services.report_service.PurchaseReport.query.filter_by") as mock_report_query:
        mock_query.return_value.first.return_value = mock_purchase
        mock_report_query.return_value.first.return_value = mock_report
        response, status = create_purchase_report_service(1, 1, "http://example.com/image.jpg", "Test report")
        assert status == 400
        assert response["message"] == "You have already reported this purchase."

    # Test case for successful report creation
    with patch("src.services.report_service.Purchase.query.filter_by") as mock_query, patch("src.services.report_service.PurchaseReport.query.filter_by") as mock_report_query:
        mock_query.return_value.first.return_value = mock_purchase
        mock_report_query.return_value.first.return_value = None
        with patch("src.services.report_service.db.session.add"), patch("src.services.report_service.db.session.commit"):
            response, status = create_purchase_report_service(1, 1, "http://example.com/image.jpg", "Test report")
            assert status == 201
            assert response["message"] == "Report created successfully"
            assert "report_id" in response

# Test the get_user_reports_service
def test_get_user_reports_service(mock_db, mock_report):
    """
    Test fetching all reports for a user.
    Verifies that all reports are retrieved successfully, or an appropriate message is returned when no reports are found.
    """

    # Test case when no reports exist for the user
    with patch("src.services.report_service.PurchaseReport.query.filter_by") as mock_query:
        mock_query.return_value.all.return_value = []
        response, status = get_user_reports_service(1)
        assert status == 200
        assert response["message"] == "No reports found for this user"

    # Test case for successful report retrieval
    with patch("src.services.report_service.PurchaseReport.query.filter_by") as mock_query:
        mock_query.return_value.all.return_value = [mock_report]
        response, status = get_user_reports_service(1)
        assert status == 200
        assert isinstance(response["reports"], list)
        assert len(response["reports"]) == 1
        assert response["reports"][0]["description"] == "Test report"

    # Test case for error when fetching reports
    with patch("src.services.report_service.PurchaseReport.query.filter_by") as mock_query:
        mock_query.side_effect = Exception("Database error")
        response, status = get_user_reports_service(1)
        assert status == 500
        assert response["message"] == "An error occurred while fetching user reports"
        assert "error" in response
