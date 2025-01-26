import pytest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash
from src.services.user_services import (
    fetch_user_data,
    change_password,
    change_username,
    change_email,
    add_favorite,
    remove_favorite,
    get_favorites,
    authenticate_user
)
from src.models import db, User, UserFavorites, CustomerAddress

# Sample user data
user_data = {
    'id': 1,
    'name': 'test_user',
    'email': 'test@example.com',
    'password': generate_password_hash('oldpassword'),
    'phone_number': '1234567890',
    'role': 'user',
    'email_verified': True
}


@pytest.fixture
def mock_user():
    """Fixture to create a mock user in the database."""
    user = User(**user_data)
    db.session.add(user)
    db.session.commit()
    return user


# Test for fetch_user_data
def test_fetch_user_data_success(mock_user):
    with patch('src.services.user_services.CustomerAddress.query.filter_by') as mock_addresses:
        mock_addresses.return_value.all.return_value = []

        data, error = fetch_user_data(mock_user.id)
        assert error is None
        assert data["user_data"]["id"] == mock_user.id


def test_fetch_user_data_user_not_found():
    data, error = fetch_user_data(999)  # User with ID 999 doesn't exist
    assert error == "User not found"
    assert data is None


# Test for change_password
def test_change_password_success(mock_user):
    with patch('src.services.user_services.check_password_hash') as mock_check_hash:
        mock_check_hash.return_value = True  # Simulating correct old password
        success, message = change_password(mock_user.id, 'oldpassword', 'newpassword')
        assert success is True
        assert message == "Password updated successfully"


def test_change_password_incorrect_old_password(mock_user):
    with patch('src.services.user_services.check_password_hash') as mock_check_hash:
        mock_check_hash.return_value = False  # Incorrect old password
        success, message = change_password(mock_user.id, 'wrongpassword', 'newpassword')
        assert success is False
        assert message == "Old password is incorrect"


# Test for change_username
def test_change_username_success(mock_user):
    new_username = "new_username"
    success, message = change_username(mock_user.id, new_username)
    assert success is True
    assert message == "Username updated successfully"
    assert mock_user.name == new_username


def test_change_username_user_not_found():
    success, message = change_username(999, "new_username")  # User with ID 999 doesn't exist
    assert success is False
    assert message == "User not found"


# Test for change_email
def test_change_email_success(mock_user):
    with patch('src.services.user_services.send_verification_email') as mock_send_email:
        new_email = "newemail@example.com"
        success, message = change_email(mock_user.id, mock_user.email, new_email)
        assert success is True
        assert message == "Email updated successfully"
        assert mock_user.email == new_email
        mock_send_email.assert_called_once_with(new_email)


def test_change_email_old_email_mismatch(mock_user):
    success, message = change_email(mock_user.id, "wrongoldemail@example.com", "newemail@example.com")
    assert success is False
    assert message == "Old email is incorrect"


# Test for add_favorite
def test_add_favorite_success(mock_user):
    with patch('src.services.user_services.UserFavorites.query.filter_by') as mock_query:
        mock_query.return_value.first.return_value = None  # No existing favorite
        success, message = add_favorite(mock_user.id, 123)
        assert success is True
        assert message == "Restaurant added to favorites"


def test_add_favorite_already_exists(mock_user):
    with patch('src.services.user_services.UserFavorites.query.filter_by') as mock_query:
        mock_query.return_value.first.return_value = MagicMock()  # Simulating existing favorite
        success, message = add_favorite(mock_user.id, 123)
        assert success is False
        assert message == "Restaurant is already in your favorites"


# Test for remove_favorite
def test_remove_favorite_success(mock_user):
    with patch('src.services.user_services.UserFavorites.query.filter_by') as mock_query:
        mock_query.return_value.first.return_value = MagicMock()  # Favorite exists
        success, message = remove_favorite(mock_user.id, 123)
        assert success is True
        assert message == "Restaurant removed from favorites"


def test_remove_favorite_not_found(mock_user):
    with patch('src.services.user_services.UserFavorites.query.filter_by') as mock_query:
        mock_query.return_value.first.return_value = None  # Favorite does not exist
        success, message = remove_favorite(mock_user.id, 123)
        assert success is False
        assert message == "Favorite not found"


# Test for get_favorites
def test_get_favorites(mock_user):
    with patch('src.services.user_services.UserFavorites.query.filter_by') as mock_query:
        mock_query.return_value.all.return_value = [MagicMock(restaurant_id=123), MagicMock(restaurant_id=456)]
        favorites = get_favorites(mock_user.id)
        assert len(favorites) == 2
        assert 123 in favorites
        assert 456 in favorites


# Test for authenticate_user
def test_authenticate_user_success(mock_user):
    success, message, user = authenticate_user(email="test@example.com", password="oldpassword")
    assert success is True
    assert message == "Authenticated successfully."
    assert user.id == mock_user.id


def test_authenticate_user_failure(mock_user):
    success, message, user = authenticate_user(email="test@example.com", password="wrongpassword")
    assert success is False
    assert message == "Incorrect password."
    assert user is None
