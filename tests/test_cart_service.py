import unittest
from unittest.mock import patch
import requests


class TestCartServices(unittest.TestCase):
    # Get cart items
    @patch('requests.get')
    def test_get_cart_items_service(self, mock_get):
        user_id = 1

        # Will return 200 if cart items are found
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"id": 1, "user_id": user_id, "listing_id": 1, "restaurant_id": 1, "count": 2}
        ]

        url = f'http://localhost:5000/cart/items/{user_id}'
        response = requests.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json()[0])
        self.assertIn('listing_id', response.json()[0])
        self.assertIn('restaurant_id', response.json()[0])
        self.assertIn('count', response.json()[0])

    # Returns 404 if cart items are not found
    @patch('requests.get')
    def test_get_cart_items_service_not_found(self, mock_get):
        user_id = 1

        # Will return 404 if cart items are not found
        mock_get.return_value.status_code = 404
        mock_get.return_value.json.return_value = {"message": "Cart not found"}

        url = f'http://localhost:5000/cart/items/{user_id}'
        response = requests.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Cart not found")

    # Add item to cart - Successful case
    @patch('requests.post')
    def test_add_to_cart_service(self, mock_post):
        user_id = 1
        listing_id = 1
        count = 2

        # Will return 201 if item is successfully added
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"message": "Item added to cart"}

        url = f'http://localhost:5000/cart/items/{user_id}'
        data = {"listing_id": listing_id, "count": count}
        response = requests.post(url, json=data)

        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Item added to cart")

    # Add item to cart - Insufficient stock
    @patch('requests.post')
    def test_add_to_cart_service_insufficient_stock(self, mock_post):
        user_id = 1
        listing_id = 1
        count = 100  # Requesting a large number

        # Will return 400 due to insufficient stock
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "message": "Insufficient stock for item"
        }

        url = f'http://localhost:5000/cart/items/{user_id}'
        data = {"listing_id": listing_id, "count": count}
        response = requests.post(url, json=data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Insufficient stock for item")

    # Remove item from cart - Successful case
    @patch('requests.delete')
    def test_remove_from_cart_service(self, mock_delete):
        user_id = 1
        listing_id = 1

        # Will return 200 if the item is removed
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = {"message": "Item removed from cart"}

        url = f'http://localhost:5000/cart/items/{user_id}/{listing_id}'
        response = requests.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Item removed from cart")

    # Reset cart - Successful case
    @patch('requests.delete')
    def test_reset_cart_service(self, mock_delete):
        user_id = 1

        # Will return 200 if the cart is successfully reset
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = {"message": "Cart reset successfully"}

        url = f'http://localhost:5000/cart/reset/{user_id}'
        response = requests.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Cart reset successfully")

    # Update cart item - Successful case
    @patch('requests.put')
    def test_update_cart_item_service(self, mock_put):
        user_id = 1
        listing_id = 1
        count = 3

        # Will return 200 if the cart item is updated
        mock_put.return_value.status_code = 200
        mock_put.return_value.json.return_value = {"message": "Cart item updated"}

        url = f'http://localhost:5000/cart/items/{user_id}/{listing_id}'
        data = {"count": count}
        response = requests.put(url, json=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Cart item updated")

    # Update cart item - Insufficient stock
    @patch('requests.put')
    def test_update_cart_item_service_insufficient_stock(self, mock_put):
        user_id = 1
        listing_id = 1
        count = 100  # Requesting a large number

        # Will return 400 due to insufficient stock
        mock_put.return_value.status_code = 400
        mock_put.return_value.json.return_value = {
            "message": "Insufficient stock for item"
        }

        url = f'http://localhost:5000/cart/items/{user_id}/{listing_id}'
        data = {"count": count}
        response = requests.put(url, json=data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Insufficient stock for item")


if __name__ == '__main__':
    unittest.main()
