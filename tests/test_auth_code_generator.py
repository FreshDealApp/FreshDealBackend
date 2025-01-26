import unittest
from unittest.mock import patch
import requests


class AuthCodeGeneratorTest(unittest.TestCase):
    # Happy Path Testing
    @patch('requests.post')
    def test_generate_and_verify_code_happy_path(self, mock_post):
        email = "test@example.com"
        ip = "192.168.1.1"
        data = {"email": email, "ip": ip}

        # Mock a successful response for generating code
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "Verification code generated successfully!"
        }

        url = f"http://localhost:5000/generate_code"
        response = requests.post(url, json=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "Verification code generated successfully!")

    # Edge Case Testing
    @patch('requests.post')
    def test_generate_code_missing_fields(self, mock_post):
        data = {"email": "test@example.com"}  # Missing IP

        # Mock a response with a missing field error
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "success": False,
            "message": "IP is required"
        }

        url = f"http://localhost:5000/generate_code"
        response = requests.post(url, json=data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "IP is required")

    @patch('requests.post')
    def test_verify_invalid_code(self, mock_post):
        email = "test@example.com"
        invalid_code = "999999"
        data = {"email": email, "code": invalid_code}

        # Mock an invalid code verification response
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "success": False,
            "message": "Code does not match"
        }

        url = f"http://localhost:5000/verify_code"
        response = requests.post(url, json=data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "Code does not match")

    # Stress Testing
    @patch('requests.post')
    def test_stress_generate_codes_for_different_ips(self, mock_post):
        email = "test@example.com"
        data = {"email": email}

        # Mock a successful response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "Verification code generated successfully!"
        }

        # Stress test: Generate codes for 1000 different IPs
        for i in range(1000):
            ip = f"192.168.1.{i+1}"
            data["ip"] = ip
            url = f"http://localhost:5000/generate_code"
            response = requests.post(url, json=data)
            self.assertEqual(response.status_code, 200)

    @patch('requests.post')
    def test_stress_verify_codes_for_different_ips(self, mock_post):
        email = "test@example.com"
        valid_code = "123456"
        data = {"email": email, "code": valid_code}

        # Mock a successful response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "Code verified successfully!"
        }

        # Stress test: Verify codes for 1000 different IPs
        for i in range(1000):
            ip = f"192.168.1.{i+1}"
            data["ip"] = ip
            url = f"http://localhost:5000/verify_code"
            response = requests.post(url, json=data)
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
