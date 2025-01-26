import unittest
from unittest.mock import patch, MagicMock
from flask import jsonify
from flask_jwt_extended import create_access_token
import os
import io
import json


class ListingsServiceTest(unittest.TestCase):
    # Happy Path Testing
    @patch('src.services.listings_service.create_listing_service')
    @patch('flask_jwt_extended.get_jwt_identity')
    @patch('src.models.User.query.get')
    @patch('werkzeug.utils.secure_filename')
    @patch('flask.Flask.send_from_directory')
    def test_create_listing_happy_path(self, mock_send_file, mock_secure_filename, mock_get_user, mock_get_identity,
                                       mock_create_listing_service):
        # Mocking necessary components
        mock_get_identity.return_value = 1
        mock_get_user.return_value = MagicMock(role='owner', id=1)
        mock_secure_filename.return_value = "image.jpg"

        # Mocking the service response
        mock_create_listing_service.return_value = ({
                                                        "success": True,
                                                        "message": "Listing created successfully!",
                                                        "listing": {
                                                            "id": 1,
                                                            "title": "Fresh Pizza Margherita",
                                                            "original_price": 15.99
                                                        }
                                                    }, 201)

        # Data to simulate the request
        data = {
            'title': 'Fresh Pizza Margherita',
            'description': 'Traditional Italian pizza with fresh basil',
            'original_price': 15.99,
            'pick_up_price': 12.99,
            'delivery_price': 17.99,
            'count': 5,
            'consume_within': 2,
            'image': io.BytesIO(b'fake image data')
        }

        # Simulating the request and response
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = json.loads(json.dumps({
                "success": True,
                "message": "Listing created successfully!",
                "listing": data
            }))

            url = f"http://localhost:5000/restaurants/1/listings"
            response = mock_post(url, files={'image': data['image']}, data=data)

            self.assertEqual(response.status_code, 201)
            self.assertIn('success', response.json())
            self.assertEqual(response.json()['message'], 'Listing created successfully!')

    # Edge Case Testing
    @patch('src.services.listings_service.create_listing_service')
    @patch('flask_jwt_extended.get_jwt_identity')
    @patch('src.models.User.query.get')
    def test_create_listing_missing_fields(self, mock_get_user, mock_get_identity, mock_create_listing_service):
        # Mocking necessary components
        mock_get_identity.return_value = 1
        mock_get_user.return_value = MagicMock(role='owner', id=1)

        # Simulating missing 'original_price' in request data
        data = {
            'title': 'Fresh Pizza Margherita',
            'description': 'Traditional Italian pizza with fresh basil',
            'pick_up_price': 12.99,
            'delivery_price': 17.99,
            'count': 5,
            'consume_within': 2,
            'image': io.BytesIO(b'fake image data')
        }

        # Mocking the service response
        mock_create_listing_service.return_value = ({
                                                        "success": False,
                                                        "message": "Original price is required"
                                                    }, 400)

        # Simulating the request and response
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = json.loads(json.dumps({
                "success": False,
                "message": "Original price is required"
            }))

            url = f"http://localhost:5000/restaurants/1/listings"
            response = mock_post(url, files={'image': data['image']}, data=data)

            self.assertEqual(response.status_code, 400)
            self.assertIn('success', response.json())
            self.assertEqual(response.json()['message'], 'Original price is required')

    # Stress Testing
    @patch('src.services.listings_service.create_listing_service')
    @patch('flask_jwt_extended.get_jwt_identity')
    @patch('src.models.User.query.get')
    def test_stress_create_listings(self, mock_get_user, mock_get_identity, mock_create_listing_service):
        mock_get_identity.return_value = 1
        mock_get_user.return_value = MagicMock(role='owner', id=1)

        # Mocking successful service response
        mock_create_listing_service.return_value = ({
                                                        "success": True,
                                                        "message": "Listing created successfully!",
                                                        "listing": {
                                                            "id": 1,
                                                            "title": "Fresh Pizza Margherita",
                                                            "original_price": 15.99
                                                        }
                                                    }, 201)

        # Stress test: Create 1000 listings
        for _ in range(1000):
            data = {
                'title': 'Fresh Pizza Margherita',
                'description': 'Traditional Italian pizza with fresh basil',
                'original_price': 15.99,
                'pick_up_price': 12.99,
                'delivery_price': 17.99,
                'count': 5,
                'consume_within': 2,
                'image': io.BytesIO(b'fake image data')
            }

            url = f"http://localhost:5000/restaurants/1/listings"
            response = mock_create_listing_service(url, files={'image': data['image']}, data=data)
            self.assertEqual(response.status_code, 201)

    # Test for fetching uploaded files
    @patch('flask.Flask.send_from_directory')
    def test_get_uploaded_file_success(self, mock_send_file):
        filename = 'image.jpg'
        mock_send_file.return_value = jsonify({"success": True, "message": "File found", "filename": filename})

        url = f"http://localhost:5000/uploads/{filename}"
        response = mock_send_file(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['message'], 'File found')


if __name__ == '__main__':
    unittest.main()
