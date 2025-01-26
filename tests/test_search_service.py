import pytest
from unittest.mock import patch
from src.services.search_service import search_restaurants, search_listings
from src.models import Restaurant, Listing


class TestSearchService:

    @patch.object(Restaurant, 'query')
    def test_search_restaurants_success(self, mock_query):
        # Arrange
        mock_restaurant = Restaurant(
            id=1,
            restaurantName="Restaurant A",
            restaurantDescription="A nice restaurant.",
            image_url="http://example.com/image.jpg",
            rating=4.5,
            category="Italian"
        )
        mock_query.filter.return_value.all.return_value = [mock_restaurant]

        query = "Restaurant A"

        # Act
        result = search_restaurants(query)

        # Assert
        assert len(result) == 1
        assert result[0]["name"] == "Restaurant A"
        assert result[0]["rating"] == 4.5
        assert result[0]["category"] == "Italian"

    @patch.object(Listing, 'query')
    def test_search_listings_success(self, mock_query):
        # Arrange
        mock_listing = Listing(
            id=1,
            restaurant_id=1,
            title="Listing 1",
            description="A great listing.",
            image_url="http://example.com/listing.jpg",
            price=19.99,
            count=5
        )
        mock_query.filter.return_value.all.return_value = [mock_listing]

        query = "Listing 1"
        restaurant_id = 1

        # Act
        result = search_listings(query, restaurant_id)

        # Assert
        assert len(result) == 1
        assert result[0]["title"] == "Listing 1"
        assert result[0]["price"] == 19.99
        assert result[0]["count"] == 5

    @patch.object(Restaurant, 'query')
    def test_search_restaurants_no_results(self, mock_query):
        # Arrange
        mock_query.filter.return_value.all.return_value = []  # No restaurants found
        query = "Nonexistent Restaurant"

        # Act
        result = search_restaurants(query)

        # Assert
        assert len(result) == 0

    @patch.object(Listing, 'query')
    def test_search_listings_no_results(self, mock_query):
        # Arrange
        mock_query.filter.return_value.all.return_value = []  # No listings found
        query = "Nonexistent Listing"
        restaurant_id = 1

        # Act
        result = search_listings(query, restaurant_id)

        # Assert
        assert len(result) == 0

    @patch.object(Restaurant, 'query')
    def test_search_restaurants_invalid_query(self, mock_query):
        # Arrange
        query = ""  # Invalid query

        # Act & Assert
        with pytest.raises(ValueError):
            search_restaurants(query)
