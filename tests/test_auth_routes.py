import unittest
from unittest.mock import patch
import requests


class AuthServiceTest(unittest.TestCase):

    # Happy Path Tests
    @patch('requests.post')
    def test_login_success(self, mock_post):
        login_data = {
            "login_type": "email",
            "password_login": True,
            "step": "skip_verification",
            "email": "user@example.com",
            "password": "userpassword123"
        }

        # Mock a successful response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "message": "Login successful"
        }

        url = "http://localhost:5000/login"
        response = requests.post(url, json=login_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "Login successful")

    @patch('requests.post')
    def test_register_success(self, mock_post):
        register_data = {
            "name_surname": "John Doe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "role": "customer"
        }

        # Mock a successful response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "User registered successfully!"
        }

        url = "http://localhost:5000/register"
        response = requests.post(url, json=register_data)

        self.assertEqual(response.status_code, 201)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "User registered successfully!")

    @patch('requests.post')
    def test_verify_email_success(self, mock_post):
        verify_data = {
            "email": "user@example.com",
            "verification_code": "123456"
        }

        # Mock a successful response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "Email verified successfully."
        }

        url = "http://localhost:5000/verify_email"
        response = requests.post(url, json=verify_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "Email verified successfully.")

    # Edge Case Tests
    @patch('requests.post')
    def test_login_invalid_email(self, mock_post):
        login_data = {
            "login_type": "email",
            "password_login": True,
            "step": "skip_verification",
            "email": "invalidemail",
            "password": "userpassword123"
        }

        # Mock a failed response
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "success": False,
            "message": "Invalid credentials"
        }

        url = "http://localhost:5000/login"
        response = requests.post(url, json=login_data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "Invalid credentials")

    @patch('requests.post')
    def test_register_invalid_email(self, mock_post):
        register_data = {
            "name_surname": "John Doe",
            "email": "invalidemail",
            "password": "SecurePass123!",
            "role": "customer"
        }

        # Mock a failed response
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "success": False,
            "message": "Invalid email format"
        }

        url = "http://localhost:5000/register"
        response = requests.post(url, json=register_data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "Invalid email format")

    @patch('requests.post')
    def test_verify_email_invalid_code(self, mock_post):
        verify_data = {
            "email": "user@example.com",
            "verification_code": "000000"
        }

        # Mock a failed response
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "success": False,
            "message": "Invalid or expired verification code"
        }

        url = "http://localhost:5000/verify_email"
        response = requests.post(url, json=verify_data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], "Invalid or expired verification code")

    # Stress Tests
    @patch('requests.post')
    def test_stress_login(self, mock_post):
        login_data = {
            "login_type": "email",
            "password_login": True,
            "step": "skip_verification",
            "email": "user@example.com",
            "password": "userpassword123"
        }

        # Mock a successful response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "message": "Login successful"
        }

        # Stress test: Simulate 1000 login requests
        for _ in range(1000):
            url = "http://localhost:5000/login"
            response = requests.post(url, json=login_data)
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
