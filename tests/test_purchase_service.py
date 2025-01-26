import pytest
from src.models import db, UserCart, Listing, Purchase, Restaurant
from src.models.purchase_model import PurchaseStatus
from src.services.purchase_service import create_purchase_order_service, handle_restaurant_response_service, \
    add_completion_image_service
from unittest.mock import patch


@pytest.fixture
def mock_db():
    # Mocked DB session setup (can be adjusted to match your app's setup)
    db.create_all()  # Creates all tables
    yield db
    db.session.remove()
    db.drop_all()


@pytest.fixture
def user_cart(mock_db):
    # Create a mock user cart with cart items
    user_id = 1
    listing = Listing(id=1, title="Test Item", count=10, pick_up_price=5.0, delivery_price=7.0)
    db.session.add(listing)
    db.session.commit()
    cart_item = UserCart(user_id=user_id, listing_id=listing.id, count=3)
    db.session.add(cart_item)
    db.session.commit()
    return cart_item


@pytest.fixture
def restaurant(mock_db):
    # Create a mock restaurant for testing
    restaurant = Restaurant(id=1, restaurantName="Test Restaurant", deliveryFee=2.0)
    db.session.add(restaurant)
    db.session.commit()
    return restaurant


def test_create_purchase_order_service(mock_db, user_cart, restaurant):
    data = {
        "is_delivery": True,
        "delivery_address": "123 Street",
        "delivery_notes": "Please deliver fast"
    }

    # Mocking for the 'create_purchase_order_service'
    with patch('src.services.purchase_service.UserCart.query.filter_by') as mock_query:
        mock_query.return_value.all.return_value = [user_cart]

        response, status_code = create_purchase_order_service(user_id=1, data=data)

        assert status_code == 201
        assert response['message'] == "Purchase order created successfully, waiting for restaurant approval"
        assert len(response['purchases']) == 1
        assert response['purchases'][0]['status'] == PurchaseStatus.PENDING.value


def test_handle_restaurant_response_service(mock_db, user_cart, restaurant):
    purchase = Purchase(user_id=1, listing_id=user_cart.listing.id, quantity=user_cart.count, total_price=15.0,
                        status=PurchaseStatus.PENDING, restaurant_id=restaurant.id)
    db.session.add(purchase)
    db.session.commit()

    # Mocking 'handle_restaurant_response_service'
    with patch('src.services.purchase_service.Purchase.query.get') as mock_query:
        mock_query.return_value = purchase
        response, status_code = handle_restaurant_response_service(purchase_id=purchase.id, restaurant_id=restaurant.id,
                                                                   action='accept')

        assert status_code == 200
        assert response['message'] == "Purchase accepted successfully"
        assert response['purchase']['status'] == PurchaseStatus.ACCEPTED.value


def test_add_completion_image_service(mock_db, user_cart, restaurant):
    purchase = Purchase(user_id=1, listing_id=user_cart.listing.id, quantity=user_cart.count, total_price=15.0,
                        status=PurchaseStatus.ACCEPTED, restaurant_id=restaurant.id)
    db.session.add(purchase)
    db.session.commit()

    # Mocking 'add_completion_image_service'
    image_url = "http://example.com/completed.jpg"
    response, status_code = add_completion_image_service(purchase_id=purchase.id, restaurant_id=restaurant.id,
                                                         image_url=image_url)

    assert status_code == 200
    assert response['message'] == "Completion image added successfully"
    assert response['purchase']['completion_image_url'] == image_url

# Additional test cases can be added below following the same Ali Rule pattern.
