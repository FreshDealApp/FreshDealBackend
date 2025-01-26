import pytest
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import MultiDict
from src.services.restaurant_service import (
    create_restaurant_service,
    get_restaurants_service,
    get_restaurant_service,
    delete_restaurant_service,
    add_comment_service,
    update_restaurant_service
)
from src.models import db, Restaurant, Purchase, RestaurantComment


@pytest.fixture
def mock_db_session():
    """Mock db session for testing."""
    with patch.object(db.session, 'add', MagicMock()) as mock_add:
        with patch.object(db.session, 'commit', MagicMock()) as mock_commit:
            yield mock_add, mock_commit


@pytest.fixture
def mock_url_for():
    """Mock the url_for function."""
    return MagicMock(return_value="http://testurl.com/image.jpg")


@pytest.fixture
def sample_restaurant():
    """Sample restaurant object for testing."""
    return Restaurant(
        id=1,
        owner_id=1,
        restaurantName="Test Restaurant",
        restaurantDescription="Description",
        longitude=0.0,
        latitude=0.0,
        category="Fast Food",
        workingDays="Monday,Tuesday",
        workingHoursStart="08:00",
        workingHoursEnd="22:00",
        listings=10,
        ratingCount=0,
        image_url="http://testurl.com/image.jpg",
        pickup=True,
        delivery=True,
        maxDeliveryDistance=10.0,
        deliveryFee=5.0,
        minOrderAmount=20.0
    )


# 1. Create Restaurant Test
def test_create_restaurant_service(mock_db_session, mock_url_for):
    form_data = MultiDict({
        'restaurantName': 'Test Restaurant',
        'restaurantDescription': 'Test Description',
        'longitude': '0.0',
        'latitude': '0.0',
        'category': 'Fast Food',
        'workingHoursStart': '08:00',
        'workingHoursEnd': '22:00',
        'workingDays': ['Monday', 'Tuesday'],
        'pickup': 'true',
        'delivery': 'true',
        'deliveryFee': '5.0',
        'minOrderAmount': '20.0',
        'maxDeliveryDistance': '10.0'
    })
    files = {}  # No file upload for now
    owner_id = 1

    response, status_code = create_restaurant_service(owner_id, form_data, files, mock_url_for)

    assert status_code == 201
    assert response["success"] is True
    assert response["message"] == "Restaurant added successfully!"
    assert response["restaurant"]["restaurantName"] == "Test Restaurant"


# 2. Get Restaurants Test
def test_get_restaurants_service(mock_db_session, sample_restaurant):
    # Mock db call
    with patch.object(Restaurant, 'query', MagicMock(return_value=[sample_restaurant])):
        owner_id = 1
        response, status_code = get_restaurants_service(owner_id)

        assert status_code == 200
        assert len(response) == 1
        assert response[0]["restaurantName"] == "Test Restaurant"


# 3. Get Single Restaurant Test
def test_get_restaurant_service(mock_db_session, sample_restaurant):
    restaurant_id = 1
    with patch.object(Restaurant, 'query', MagicMock(return_value=sample_restaurant)):
        response, status_code = get_restaurant_service(restaurant_id)

        assert status_code == 200
        assert response["restaurantName"] == "Test Restaurant"
        assert response["ratingCount"] == 0


# 4. Delete Restaurant Test
def test_delete_restaurant_service(mock_db_session, sample_restaurant):
    restaurant_id = 1
    owner_id = 1
    with patch.object(Restaurant, 'query', MagicMock(return_value=sample_restaurant)):
        response, status_code = delete_restaurant_service(restaurant_id, owner_id)

        assert status_code == 200
        assert response["success"] is True
        assert response["message"] == f"Restaurant with ID {restaurant_id} successfully deleted."


# 5. Add Comment Test
def test_add_comment_service(mock_db_session, sample_restaurant):
    restaurant_id = 1
    user_id = 1
    data = {
        "comment": "Great place!",
        "rating": 5,
        "purchase_id": 1
    }
    with patch.object(Restaurant, 'query', MagicMock(return_value=sample_restaurant)):
        with patch.object(Purchase, 'query', MagicMock(return_value=MagicMock(user_id=user_id))):
            response, status_code = add_comment_service(restaurant_id, user_id, data)

            assert status_code == 201
            assert response["success"] is True
            assert response["message"] == "Comment added successfully"


# 6. Update Restaurant Test
def test_update_restaurant_service(mock_db_session, mock_url_for, sample_restaurant):
    restaurant_id = 1
    owner_id = 1
    form_data = MultiDict({
        'restaurantName': 'Updated Restaurant',
        'restaurantDescription': 'Updated Description',
        'longitude': '1.0',
        'latitude': '1.0',
        'category': 'Italian',
        'workingHoursStart': '09:00',
        'workingHoursEnd': '23:00',
        'workingDays': ['Wednesday', 'Thursday'],
        'pickup': 'false',
        'delivery': 'true',
        'deliveryFee': '8.0',
        'minOrderAmount': '25.0',
        'maxDeliveryDistance': '15.0'
    })
    files = {}
    with patch.object(Restaurant, 'query', MagicMock(return_value=sample_restaurant)):
        response, status_code = update_restaurant_service(restaurant_id, owner_id, form_data, files, mock_url_for)

        assert status_code == 200
        assert response["success"] is True
        assert response["message"] == "Restaurant updated successfully!"
        assert response["restaurant"]["restaurantName"] == "Updated Restaurant"

