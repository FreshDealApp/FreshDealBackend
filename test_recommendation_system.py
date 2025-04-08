from recommendation_system import get_recommendations_for_user
from app import create_app
# Testing recommendation system to see recommendated listing for each user by searching with their user_id

# Create an app instance
app = create_app()

# Test with a specific user_id
user_id = 56

with app.app_context():  # Ensure we are inside the Flask application context
    recommendations = get_recommendations_for_user(user_id)

# Print the recommendations
print(recommendations)
