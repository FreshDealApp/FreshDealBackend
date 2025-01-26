import pytest
from unittest.mock import patch
from werkzeug.datastructures import FileStorage
from src.models import Restaurant, User
from src.services.listings_service import create_listing_service

@pytest.fixture
def mock_data():
    # Create mock data for the test
    restaurant_id = 1
    owner_id = 1
    form_data = {
        'title': 'Fresh Pizza Margherita',
        'description': 'Traditional Italian pizza with fresh basil',
        'original_price': '15.99',
        'pick_up_price': '12.99',
        'delivery_price': '17.99',
        'count': '5',
        'consume_within': '2'
    }
    file_obj = FileStorage(filename='pizza_image.jpg')  # Mocked file object for the image

    mock_restaurant = Restaurant(id=restaurant_id, owner_id=owner_id)
    mock_owner = User(id=owner_id, role="owner")

    return {
        'restaurant_id': restaurant_id,
        'owner_id': owner_id,
        'form_data': form_data,
        'file_obj': file_obj,
        'mock_restaurant': mock_restaurant,
        'mock_owner': mock_owner
    }

def test_create_listing_service(mock_data):
    # Unpack mock data
    restaurant_id = mock_data['restaurant_id']
    owner_id = mock_data['owner_id']
    form_data = mock_data['form_data']
    file_obj = mock_data['file_obj']

    # Mock Database Queries
    with patch('src.models.Restaurant.query.get') as mock_get_restaurant, \
         patch('src.models.User.query.get') as mock_get_user, \
         patch('src.models.db.session.commit') as mock_commit, \
         patch('src.models.Listing.create') as mock_create_listing:

        # Simulate Restaurant query returning the mock restaurant object
        mock_get_restaurant.return_value = mock_data['mock_restaurant']

        # Simulate User query returning the mock user object (owner)
        mock_get_user.return_value = mock_data['mock_owner']

        # Call the create listing service
        response, status_code = create_listing_service(
            restaurant_id=restaurant_id,
            owner_id=owner_id,
            form_data=form_data,
            file_obj=file_obj,
            url_for_func=None  # No need for image_url in this test
        )

        # Assertions for response
        assert response['success'] is True
        assert response['message'] == "Listing added successfully!"
        assert 'listing' in response
        assert response['listing']['title'] == form_data['title']
        assert response['listing']['description'] == form_data['description']
        assert response['listing']['original_price'] == float(form_data['original_price'])

        # Ensure that create method was called with correct values
        mock_create_listing.assert_called_once_with(
            restaurant_id=restaurant_id,
            title=form_data['title'],
            description=form_data['description'],
            image_url=None,
            original_price=float(form_data['original_price']),
            pick_up_price=float(form_data['pick_up_price']),
            delivery_price=float(form_data['delivery_price']),
            count=int(form_data['count']),
            consume_within=int(form_data['consume_within'])
        )
