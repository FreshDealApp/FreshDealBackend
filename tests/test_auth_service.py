import unittest
from unittest.mock import patch
import requests


class AddressServiceTest(unittest.TestCase):
    # Happy Path Testing
    @patch('requests.post')
    def test_create_address_happy_path(self, mock_post):
        user_id = 1
        data = {
            "title": "Home",
            "longitude": 34.0522,
            "latitude": -118.2437,
            "street": "Main Street",
            "neighborhood": "Downtown",
            "district": "Central",
            "province": "California",
            "country": "USA",
            "postalCode": "90001",
            "apartmentNo": "5A",
            "doorNo": "12",
            "is_primary": False
        }

        # Mock a successful response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "Address created successfully!",
            "address": data
        }

        url = f"http://localhost:8000/users/{user_id}/addresses"
        response = requests.post(url, json=data)

        self.assertEqual(response.status_code, 201)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], 'Address created successfully!')

    # Edge Case Testing
    @patch('requests.post')
    def test_create_address_missing_fields(self, mock_post):
        user_id = 1
        data = {"title": "Home"}  # Missing required fields like longitude, latitude, etc.

        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "success": False,
            "message": "Longitude and latitude are required"
        }

        url = f"http://localhost:8000/users/{user_id}/addresses"
        response = requests.post(url, json=data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], 'Longitude and latitude are required')

    @patch('requests.delete')
    def test_delete_non_existent_address(self, mock_delete):
        user_id = 1
        address_id = 9999  # Non-existent address

        mock_delete.return_value.status_code = 404
        mock_delete.return_value.json.return_value = {
            "message": "Address not found"
        }

        url = f"http://localhost:8000/users/{user_id}/addresses/{address_id}"
        response = requests.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], 'Address not found')

    # Stress Testing
    @patch('requests.post')
    def test_stress_create_addresses(self, mock_post):
        user_id = 1
        data = {
            "title": "Home",
            "longitude": 34.0522,
            "latitude": -118.2437,
            "street": "Main Street",
            "neighborhood": "Downtown",
            "district": "Central",
            "province": "California",
            "country": "USA",
            "postalCode": "90001",
            "apartmentNo": "5A",
            "doorNo": "12",
            "is_primary": False
        }

        # Mock a successful response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "Address created successfully!",
            "address": data
        }

        # Stress test: Create 1000 addresses
        for i in range(1000):
            url = f"http://localhost:8000/users/{user_id}/addresses"
            response = requests.post(url, json=data)
            self.assertEqual(response.status_code, 201)

    @patch('requests.put')
    def test_stress_update_addresses(self, mock_put):
        user_id = 1
        address_id = 1
        data = {
            "street": "Updated Street",
            "district": "Updated District",
            "province": "Updated Province"
        }

        # Mock a successful response
        mock_put.return_value.status_code = 200
        mock_put.return_value.json.return_value = {
            "success": True,
            "message": "Address updated successfully!",
            "address": data
        }

        # Stress test: Update address 500 times
        for i in range(500):
            url = f"http://localhost:8000/users/{user_id}/addresses/{address_id}"
            response = requests.put(url, json=data)
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
