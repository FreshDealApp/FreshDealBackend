import os
import unittest
from unittest.mock import patch
from flask import Flask
from flask_jwt_extended import create_access_token
from app import create_app  # Call your Flask app factory function here.
import requests


class PurchaseOrderServiceTest(unittest.TestCase):

    def setUp(self):
        # Set required environment variables for testing
        os.environ["DB_SERVER"] = "localhost"
        os.environ["DB_NAME"] = "test_db"
        os.environ["DB_USERNAME"] = "test_user"
        os.environ["DB_PASSWORD"] = "test_password"
        os.environ["DB_DRIVER"] = "sqlite"
        os.environ["JWT_SECRET_KEY"] = "test_secret_key"

        # Create Flask app in testing mode
        self.app = create_app(testing=True)
        self.client = self.app.test_client()
        self.jwt_token = self._generate_jwt_token()

    def _generate_jwt_token(self):
        """Generate a valid JWT token for testing."""
        with self.app.app_context():
            return create_access_token(identity="test_user")

    # Happy Path Testing
    @patch('requests.post')
    def test_create_purchase_order_happy_path(self, mock_post):
        """Test creating a valid purchase order."""
        payload = {
            "is_delivery": True,
            "delivery_address": "123 Main St",
            "delivery_notes": "Leave at the door."
        }

        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "Purchase order created successfully!",
            "purchases": payload
        }

        response = self.client.post(
            "/purchase",
            json=payload,
            headers={"Authorization": f"Bearer {self.jwt_token}"}
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("message", response.json)
        self.assertIn("purchases", response.json)

    # Edge Case Testing
    @patch('requests.post')
    def test_create_purchase_order_missing_address(self, mock_post):
        """Test creating an order with a missing delivery address."""
        payload = {
            "is_delivery": True  # Address is missing.
        }

        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "success": False,
            "message": "Cart is empty or delivery address required for delivery orders"
        }

        response = self.client.post(
            "/purchase",
            json=payload,
            headers={"Authorization": f"Bearer {self.jwt_token}"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.json)
        self.assertEqual(
            response.json["message"],
            "Cart is empty or delivery address required for delivery orders"
        )

    # Stress Testing
    @patch('requests.post')
    def test_stress_create_multiple_orders(self, mock_post):
        """Stress test: Sending multiple orders simultaneously."""
        payload = {
            "is_delivery": False,
            "pickup_notes": "I will pick it up at 6 PM."
        }

        # Mock a successful response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "Purchase order created successfully!"
        }

        for _ in range(50):  # Send 50 requests simultaneously.
            response = self.client.post(
                "/purchase",
                json=payload,
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            self.assertEqual(response.status_code, 201)

    # Unauthorized Access Testing
    @patch('requests.post')
    def test_unauthorized_access(self, mock_post):
        """Test unauthorized access with an invalid JWT token."""
        payload = {
            "is_delivery": False,
            "pickup_notes": "I will pick it up at 6 PM."
        }

        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {
            "msg": "Missing authorization header"
        }

        response = self.client.post(
            "/purchase",
            json=payload,
            headers={"Authorization": "Bearer invalid_token"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("msg", response.json)
        self.assertEqual(response.json["msg"], "Missing authorization header")


if __name__ == "__main__":
    unittest.main()
