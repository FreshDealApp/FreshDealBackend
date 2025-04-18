import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import os
import pyodbc
from dotenv import load_dotenv


def load_purchase_data():
    """Load purchase data from SQL Server database."""
    load_dotenv()  # Load environment variables from .env file

    required_env_vars = ['DB_DRIVER', 'DB_SERVER', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']
    for var in required_env_vars:
        if not os.getenv(var):
            print(f"Environment variable '{var}' is not set.")
            return pd.DataFrame()

    connection_string = (
        f"DRIVER={{{os.getenv('DB_DRIVER')}}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        "Encrypt=yes;TrustServerCertificate=no;Authentication=SqlPassword"
    )

    conn = None
    try:
        conn = pyodbc.connect(connection_string)
        query = """
        SELECT user_id, listing_id 
        FROM purchases
        """
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("Warning: Purchase data loaded successfully but is empty.")
        else:
            print("Purchase data loaded successfully.")
            print(df.head())  # Debug için ilk 5 satırı göster

        return df
    except Exception as e:
        print(f"An error occurred while loading purchase data: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            conn.close()


def create_user_item_matrix(df):
    """Create a user-item matrix of purchase frequencies."""
    if df.empty:
        raise ValueError("Error: Received empty dataframe. Cannot create user-item matrix.")

    df.columns = df.columns.str.lower()
    required_columns = {'user_id', 'listing_id'}
    if not required_columns.issubset(df.columns):
        print(f"Error: Missing required columns in DataFrame. Found columns: {df.columns.tolist()}")
        raise KeyError("Missing 'user_id' or 'listing_id' columns in DataFrame.")

    return pd.crosstab(df['user_id'], df['listing_id'])


def train_knn_model(user_item_matrix, n_neighbors=5):
    """Train KNN model on user-item matrix."""
    if user_item_matrix.empty:
        raise ValueError("Error: Cannot train KNN model on an empty user-item matrix.")
    model = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
    model.fit(user_item_matrix.T)
    return model


def get_recommendations(listing_id, user_item_matrix, knn_model, df, n=5):
    """Get top N recommendations for a given listing_id."""
    if listing_id not in user_item_matrix.columns:
        print(f"Warning: Listing ID {listing_id} not found in user-item matrix.")
        return []

    item_idx = list(user_item_matrix.columns).index(listing_id)
    item_vector = user_item_matrix.iloc[:, item_idx].values.reshape(1, -1).T

    distances, indices = knn_model.kneighbors(item_vector.T)
    similar_items = [int(user_item_matrix.columns[idx]) for idx in indices[0][1:]]
    purchase_counts = [len(df[df['listing_id'] == item]) for item in similar_items[:n]]

    recommendations = [
        {"item_id": item, "purchases": count}
        for item, count in zip(similar_items[:n], purchase_counts)
    ]
    return recommendations


class RecommendationSystem:
    def __init__(self):
        self.df = load_purchase_data()
        self.user_item_matrix = create_user_item_matrix(self.df)
        self.knn_model = train_knn_model(self.user_item_matrix)

    def get_recommendations_for_item(self, item_id):
        recommendations = get_recommendations(item_id, self.user_item_matrix, self.knn_model, self.df)
        return {
            "item_id": item_id,
            "recommendations": recommendations
        }


def test_recommendation_system():
    """Pytest test function for recommendation system."""
    df = load_purchase_data()
    assert not df.empty, "Test failed: Loaded purchase DataFrame is empty."
    print(f"Loaded {len(df)} rows for testing.")

    user_item_matrix = create_user_item_matrix(df)
    knn_model = train_knn_model(user_item_matrix)

    test_item = 2
    recommendations = get_recommendations(test_item, user_item_matrix, knn_model, df)

    assert isinstance(recommendations, list), "Should return a list"
    assert len(recommendations) > 0, "Should return recommendations"
    assert isinstance(recommendations[0], dict), "Should return dictionary format"
    assert "item_id" in recommendations[0], "Should contain item_id"
    assert "purchases" in recommendations[0], "Should contain purchases count"


if __name__ == "__main__":
    recommender = RecommendationSystem()
    test_items = [2, 15, 30, 45]
    for item in test_items:
        result = recommender.get_recommendations_for_item(item)
        print(f"\nPeople who ordered listing #{item} also ordered:")
        for rec in result['recommendations']:
            print(f"- Listing #{rec['item_id']} (ordered {rec['purchases']} times)")
